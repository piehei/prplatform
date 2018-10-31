from django.contrib import messages
import re

from prplatform.users.models import StudentGroup
from prplatform.submissions.models import Answer


def handle_group_file(request, ctx, form):
    cd = form.cleaned_data
    try:
        contents = cd['group_file'].read().decode('utf-8')
    except Exception as e:
        print("an exception occurred")
        print(e)
        messages.error(request, "The uploaded file could not be parsed. Make sure it's either ASCII or UTF-8 encoded.")
        return

    moodle_format = cd['moodle_format']

    groups = {}
    used_usernames = []
    group_file_is_valid = True

    if not moodle_format:
        for row in contents.strip().split("\n"):
            parts = row.strip().split(",")
            if len(parts) == 0:
                continue
            name = parts[0]
            usernames = parts[1:]

            if name in groups:
                messages.error(request, f'Group name "{name}" appears twice in the file. Cannot continue.')
                group_file_is_valid = False
            else:
                groups[name] = usernames

            for username in usernames:
                if username in used_usernames:
                    messages.error(request, f'Username "{username}" appears in more than one group. Cannot continue.')
                    group_file_is_valid = False
                used_usernames.append(username)

    # Moodle format fiel header row:
    # ['Group ID', 'Group Name', 'Group Size', 'Group Description', 'Assigned teacher Username', 'Assigned teacher Firstname',
    # 'Assigned teacher Lastname', 'Assigned teacher Email', 'Member 1 Username', 'Member 1 ID Number', 'Member 1 Firstname',
    # "'Member 1 Lastname', 'Member 1 Email', 'Member 2 Username', 'Member 2 ID Number', 'Member 2 Firstname', 'Member 2 Lastname',
    # 'Member 2 Email', 'Member 3 Username', 'Member 3 ID Number', 'Member 3 Firstname', 'Member 3 Lastname', 'Member 3 Email']

    if moodle_format:
        rows = contents.split("\n")
        sep = ";"
        header_row_number = 0
        if "sep=" in rows[0]:
            sep = rows[0].strip().split("sep=")[1]
            headers = rows[1].strip().split(sep)
            header_row_number = 1
        else:
            headers = rows[0].strip().split(sep)

        messages.info(request, f'Using {sep} as the separator')

        for group_row in rows[header_row_number + 1:]:
            if sep not in group_row:  # empty row or something
                continue
            columns = group_row.strip().split(sep)
            group_name = ""

            for i in range(len(columns)):
                field = columns[i].strip('"')
                if i >= len(headers):  # no header -> extra field
                    continue
                field_name = headers[i]

                if len(field) == 0:  # empty fields on a row
                    continue

                if field_name == "Group Description":
                    group_name = field[0:10]
                    if group_name in groups:
                        messages.error(request, f'Group name "{group_name}" appears twice in the file. Cannot continue.')
                        group_file_is_valid = False
                    else:
                        groups[group_name] = []

                if re.compile('Member [0-9] Email').fullmatch(field_name):
                    username_now = field
                    if username_now in used_usernames:
                        messages.error(request, f'Username "{field}" appears in more than one group. Cannot continue.')
                        group_file_is_valid = False
                    groups[group_name].append(username_now)
                    used_usernames.append(username_now)

    if group_file_is_valid:
        print("Group file IS valid! Can continue!")

        messages.info(request, f'Found {len(groups)} groups in the CSV file.')

        for group_name in groups:
            existing_group = StudentGroup.objects.filter(course=ctx['course'], name=group_name).first()
            if existing_group:
                existing_usernames = existing_group.student_usernames
                existing_group.student_usernames = groups[group_name]
                existing_group.save()
                messages.warning(request, f'Updated group: "{existing_group.name}" with students: {existing_usernames} --> {existing_group.student_usernames}')
            else:
                new_group = StudentGroup.objects.create(course=ctx['course'],
                                                        name=group_name,
                                                        student_usernames=groups[group_name])
                messages.success(request, f'Created group: "{new_group.name}" with students: {new_group.student_usernames}')
    else:
        messages.error(request, "Group file was not valid. Cannot do anything.")


def create_stats(ctx, include_textual_answers=False, pad=False):
    re = ctx['re']
    print("CREATE STATS FOR:",re)
    d = {}

    HEADERS = []

    # for index, orig_sub in enumerate(ctx['orig_subs']):
    for index, orig_sub in enumerate(ctx['orig_subs']):
        key = orig_sub.pk
        d[key] = {'orig_sub': orig_sub, 'numerical_avgs': [], 'reviews_for': [], 'reviews_by': [], 'textual_answers': []}
        d[key]['reviews_by'] = re.last_reviews_by(orig_sub.submitter_user)
        d[key]['reviews_for'] = re.last_reviews_for(orig_sub.submitter_user)

    HEADERS.append('Submitter')
    HEADERS.append('Reviews by submitter')
    HEADERS.append('Reviews for submitter')

    numeric_questions = re.questions.exclude(choices__len=0)

    # TODO: calculate on the DBMS
    if numeric_questions:
        for nq in numeric_questions:

            print("\nnq:", nq)
            HEADERS.append(f"Q: {nq.text}")

            for row in d:
                review_pks = d[row]['reviews_for'].values_list('pk', flat=True)
                print("answer_pks:", review_pks)

                answer_values = Answer.objects.filter(question=nq,
                                                      submission__pk__in=review_pks) \
                                              .values_list('value_choice', flat=True)

                print("answer_values:", answer_values)

                if answer_values:
                    avg = sum([int(a) for a in answer_values])/len(answer_values)
                    print("avg is:", avg)
                    d[row]['numerical_avgs'].append(avg)

    # collect whatever textual questions available
    # collect answers to them
    # append answer texts into 'textual_answers' for each submitter
    if include_textual_answers:
        textual_questions = re.questions.filter(choices__len=0)
        if textual_questions:
            for (index, tq) in enumerate(textual_questions):
                for os in ctx['orig_subs']:
                    for review_sub in os.reviews.all():
                        textual_answer = review_sub.answers.filter(question=tq).first()
                        if textual_answer:
                            d[os.pk]['textual_answers'].append(f"{review_sub.submitter}: {textual_answer.value_text}")

                max_answer_count = max([len(x['textual_answers']) for x in d.values()])
                print('max answer count is: ', max_answer_count)
                HEADERS += [f"A{index + 1}: {num}" for num in range(1, max_answer_count + 1)]

    max_review_range = range(1, max([len(x['reviews_for']) for x in d.values()]) + 1)

    ctx['max_review_range'] = max_review_range

    if pad:
        max_textual_answer_count = max([len(x['textual_answers']) for x in d.values()])
        for row in d:

            difference = len(numeric_questions) - len(d[row]['numerical_avgs'])
            if difference != 0:
                d[row]['numerical_avgs'] += difference * [None]

            # difference = len(max_review_range) - len(d[row]['reviews_for'])
            # if difference != 0:
                # d[row]['reviews_for'] += difference * [None]

            difference = max_textual_answer_count - len(d[row]['textual_answers'])
            if difference != 0:
                d[row]['textual_answers'] += difference * [None]

    # for row in d:
    #     print(d[row])
    # for row in d:
    #     print(len(d[row]['textual_answers']), len(d[row]['numerical_avgs']))
    # print("HEADERS ARE:")
    # print(HEADERS)
    d['headers'] = HEADERS
    return d
