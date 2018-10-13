from django.contrib import messages
import re

from prplatform.users.models import StudentGroup


def handle_group_file(request, ctx, form):
    cd = form.cleaned_data

    contents = cd['group_file'].read().decode('utf-8')

    moodle_format = False
    if 'moodle_format' in request.POST:
        moodle_format = True

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
        sep = rows[0].split("sep=")[1]
        headers = rows[1].split(sep)

        messages.info(request, f'Using {sep} as the separator')

        for group_row in rows[2:]:
            parts = group_row.split(sep)
            group_name = ""
            for i in range(len(parts)):
                field = parts[i].strip('"')
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
                messages.success(request, f'Created group: "{new_group}" with students: {new_group.student_usernames}')
    else:
        messages.error(request, "Group file was not valid. Cannot do anything.")
