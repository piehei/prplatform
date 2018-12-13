from django.db import models
from django.core.exceptions import EmptyResultSet

from .models import (
        OriginalSubmission,
        ReviewSubmission,
    )

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import (
        StudentGroup,
        User,
    )
from prplatform.exercises.models import (
        ReviewExercise,
    )


class ReviewLockManager(models.Manager):

    def create_rlock(self, exercise, user, group=None):
        print(f"create_lock called for {exercise} {user} {group}")

        if exercise.use_groups and not group:
            raise Exception("Group info doesn't match")

        if not exercise.use_groups and group:
            raise Exception("Group info doesn't match")

        if exercise.type == ReviewExercise.RANDOM:
            print("type is RANDOM")

            """
                TODO: pick original submission based on some other heuristics
                      than just random value. something that has not received any
                      reviews?
            """

            # this is all _last_ submissions by other submitters sorted by review count
            osub_candidates = OriginalSubmission.objects \
                                           .filter(exercise=exercise.reviewable_exercise) \
                                           .annotate(models.Count('reviewlocks')) \
                                           .order_by('reviewlocks__count', 'created')

            # osub_candidates are now ordered so that first item has least reviewlocks
            # was created the longest time ago



            # ATTENTION !!!!!!!!!!
            # the query just above *CANNOT* be joined with the order_by/distinct queries
            # that's why we need two queries

            print(f"{osub_candidates.count()} -- before max_rev_per_sub exlude")
            osub_candidates = osub_candidates.exclude(reviewlocks__count__gte=exercise.max_reviews_per_submission)
            print(f"{osub_candidates.count()} -- after max_rev_per_sub exlude")

            if exercise.reviewable_exercise.use_groups:
                latest_submission_ids = OriginalSubmission.objects.filter(exercise=exercise.reviewable_exercise) \
                                                          .values('id') \
                                                          .order_by('submitter_group_id', '-created') \
                                                          .distinct('submitter_group_id')
                osub_candidates = osub_candidates.exclude(
                                                    submitter_group=exercise.course.find_studentgroup_by_user(user)) \
                                                 .filter(id__in=latest_submission_ids)

            else:
                latest_submission_ids = OriginalSubmission.objects.filter(exercise=exercise.reviewable_exercise) \
                                                          .values('id') \
                                                          .order_by('submitter_user_id', '-created') \
                                                          .distinct('submitter_user_id')
                osub_candidates = osub_candidates.exclude(submitter_user=user) \
                                                 .filter(id__in=latest_submission_ids)

            previous_revsub_ids = exercise.last_reviews_by(user).values('reviewed_submission__id')
            print(f"previous_revsub_ids: {previous_revsub_ids}")
            print(f"{osub_candidates.count()} -- before prev id exlude")
            osub_candidates = osub_candidates.exclude(pk__in=previous_revsub_ids)
            print(f"{osub_candidates.count()} -- after prev id exlude")
            osub_candidates = osub_candidates.filter(state=OriginalSubmission.READY_FOR_REVIEW)
            print(f"{osub_candidates.count()} -- after READY_FOR_REVIEW filter")

            if osub_candidates.count() == 0:
                raise EmptyResultSet("nothing to review")

            reviewable = osub_candidates.first()

        return self.create(user=user,
                           group=group,
                           review_exercise=exercise,
                           original_submission=reviewable)


class ReviewLock(TimeStampedModel):

    objects = ReviewLockManager()

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(StudentGroup, null=True, default=None, on_delete=models.CASCADE)
    original_submission = models.ForeignKey(OriginalSubmission, related_name="reviewlocks", on_delete=models.CASCADE)
    review_exercise = models.ForeignKey(ReviewExercise, on_delete=models.CASCADE)
    review_submission = models.ForeignKey(ReviewSubmission, null=True, default=None, on_delete=models.CASCADE)

    @property
    def owner(self):
        if self.group:
            return f"{self.group}"
        return f"self.user"

