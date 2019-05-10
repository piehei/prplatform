prplatform
==========

This is a peer-review web app for university courses etc. It allows teachers to create
exercises, students to submit exercises, teachers to review students' submissions,
students to peer-review other students' submissions etc. Groups are supported. The
app can be used standalone or to peer-review exercises submitted in the A+ learning platform.


This system is developed in Python programming language and PostreSQL database with the Django
web framework utilizing a project scaffold created by Cookiecutter. You may find the original
Cookiecutter documentation in README_cookiecutter.rst.

:License: MIT

Teacher manual
=============

Creating a course

When you want your course to be added to the system, you first have to login. After that you can
request the administrator of the system to create you a course. After the course has been created
it will show up on the front page of the system and you will be able to start creating exercise.
In the beginning, you can mark the course hidden so that students or other users of the system
don't find unfinished content.

Exercises

The system distinguishes between two different kinds of exercises, Submission exercises and Review
exercises. These two kinds of exercises have multiple different types which will be covered in the
next section. Exercises can be completed in groups or as individuals. How groups work is covered
under the Groups title below.

Submission exercise
- This is where students return some original content to the system, eg. exercise answer, some
  code, seminar presentation slides, and so on. This is not peer-reviewing. This is the thing
  that will be peer-reviewed.

- Types:
    - Students submit a free text form
    - Students submit a file
    - Students submit something in the A+ e-learning system that the system itself, A+, grades
      automatically via eg. mooc-grader service. Every time students submit something in A+, that
      system contacts PRP. PRP then fetches the submission from A+ and if it has a passing score,
      a new submission is created for the user.
      This exercise type requires the teacher to provide her own A+ API key in the "Edit course"
      page found from the course frontpage.
    - Students don't submit anything, group peer-review (this is explained in the Review exercise
      types)

Review exercise
- This is where peer-reviewing happens. Students do a peer-review where they answer questions
  defined by the teacher. It is crucial to understand that the system requires a mapping from a
  Review exercise to a Submission exercise, in other words there always has to be a Submission exercise where
  the students return something before there can be a Review exercise.
  When doing the peer-review, the sudents are presented with the submission made by the target
  of the peer-review (other student).


- Types (who peer-reviews who):
  - Random. System "randomly" chooses one submission for the student to be peer-reviewed. The
    system prefers oldest with least peer-reviews.
  - Choose. Students are presented with a dropdown list of all submissions in the Submission
    exercise and they can freely choose who to peer-review.
  - Group. Students peer-review other members in their own group. This Review exercise type is
    useful when students are supposed to give feedback to other group members for eg. participating
    in a group work or grade them for the teacher. Students can also give feedback to themselves
    if the Review exercise is configured so. In this Review exercise type the students don't really
    have anything to return to a Submission exercise. When this type is used, the corresponding
    Submission exercise needs to have the last type listed above in Submission exercise types.
    With that type, the students don't return anything to the Submission exercise but the system
    itself creates a dummy submission for each student in all groups.

- Questions
  Every Review exercise has at least one question. The type of the question determines how it is
  answered. The student can either answer in free text, choose an option from a list of options
  presented by the question, or upload a file. Every Review exercise can have multiple questions.
  The teacher can choose for each question separately whether the peer-reviewed student will see
  the answer (so for instance there could be three questions which the peer-reviewed student
  sees the answers for and one question which only the teacher can view).

- Peer-review availability time and visibility
  The teacher can decide when the feedback/peer-review is available for the peer-reviewed student
  to see. The student can be required to complete some amount of peer-reviews herself before
  seeing peer-reviews about herself. It is also possible to define a clear date and time after
  which everyone can see the peer-reviews for themselves. These two options can be combined
  (require peer-reviews and after date).
  The object of the peer-review (who was pee-reviewed) never sees who submitted the peer-review.

Groups
- The system supports groups. Groups are formed in another system outside of PRP and then uploaded
  to PRP using a csv file. The supported csv file types are described in the "Edit group" page
  of each course.
- One course has one set of groups. Groups can be used on exercise-by-exercise basis so not all
  exercises need to use groups. When an exercise uses groups, students will create submissions
  by their group. The submission page will tell the students in which group they belong to etc.
- When a submission is made by a group, all members of that group can view that submission. All
  members of the group can also view all peer-reviews for that submission.
- Groups can be modified any time by uploading a new csv file. This affects both old and new
  submissions (if someone is added to a group, she will see earlier submissions by the group etc.)

Usage with A+
- ...
