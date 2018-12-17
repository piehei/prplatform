from django.db import models
from django.db.models import Count
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

            """
                TODO: this algo does NOT take into account a situation where one updates their review
                      which causes two reviews to be available for an original submission
            """

            # all original submissions that *could* be the target of the review
            # annotated with their existing review and reviewlock counts
            # the queryset is ordered in ascending order by reviews_and_locks sum and creation date
            # ---> first item is the one with least reviews/locks and oldest creation date
            osub_candidates = OriginalSubmission.objects \
                                                .filter(exercise=exercise.reviewable_exercise) \
                                                .annotate(
                                                    reviews_and_locks=Count('reviewlocks', distinct=True)+Count('reviews', distinct=True)
                                                    ) \
                                                .order_by(
                                                    'reviews_and_locks',
                                                    'created'
                                                    )

            # ATTENTION !!!!!!!!!!
            # the query just above *CANNOT* be joined with the order_by/distinct queries
            # that's why we need two queries

            # print(f"{osub_candidates.count()} -- before max_rev_per_sub exlude")
            # print(osub_candidates)
            osub_candidates = osub_candidates.exclude(reviews_and_locks__gte=exercise.max_reviews_per_submission)
            # print(f"{osub_candidates.count()} -- after max_rev_per_sub exlude")
            # print(osub_candidates)

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
            # print(f"previous_revsub_ids: {previous_revsub_ids}")
            # print(f"{osub_candidates.count()} -- before prev id exlude")
            # print(osub_candidates)
            osub_candidates = osub_candidates.exclude(pk__in=previous_revsub_ids)
            # print(f"{osub_candidates.count()} -- after prev id exlude")
            # print(osub_candidates)
            osub_candidates = osub_candidates.filter(state=OriginalSubmission.READY_FOR_REVIEW)
            # print(f"{osub_candidates.count()} -- after READY_FOR_REVIEW filter")
            # print(osub_candidates)

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
        return f"{self.user}"

    def __str__(self):
        return f"{self.user} {self.group} -- {self.original_submission}"

