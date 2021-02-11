from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from codershq.users.scoring.score import CHQScore
from codershq.users.validators import validate_github_profile

# from codershq.users.tasks import update_github_score

class User(AbstractUser):
    """Default user for Coders Headquarters."""

    #: First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    bio = models.TextField(_("Biography"), blank=True, max_length=500)
    cv = models.FileField(_("User's CV"), null=True, blank=True, upload_to="cv")
    academic_qualification = models.CharField(_("User's highest qualification"), blank=True, max_length=30)
    academic_qualification_file = models.FileField(null=True, blank=True, upload_to="academic")
    github_profile = models.CharField(_("User's GitHub profile"), blank=True, max_length=255,
                                      validators=[validate_github_profile])
    github_updated = models.DateTimeField(null=True, blank=True)
    github_score = models.IntegerField(null=False, default=0)
    front_end_score = models.IntegerField(null=False, default=20)
    back_end_score = models.IntegerField(null=False, default=20)
    database_score = models.IntegerField(null=False, default=20)
    devops_score = models.IntegerField(null=False, default=20)
    mobile_score = models.IntegerField(null=False, default=20)

    first_name = None  # type: ignore
    last_name = None  # type: ignore

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    @property
    def github_username(self):
        split_url = self.github_profile.split('/')
        if split_url[-1] == '':
            user_name = split_url[-2]
        else:
            user_name = split_url[-1]
        return user_name

    def save(self, *args, **kwargs):
        """
        Fails if score does not have a total of 100 and if news source is not available.
        """

        # # raise error if score doesnt add to 100
        # if self.total_self_score() != 100:
        #     raise ScoreNot100()

        # if profile has a github_profile
        if self.github_profile != '':
            # if profile score was updated
            chq_score = CHQScore(settings.GITHUB_TOKEN)
            if self.github_updated != None:
                # only get score when enough time has passed
                if timezone.now()-timezone.timedelta(seconds=24) >= self.github_updated <= timezone.now():
                    # save current score and use it if api call fails
                    self.github_score = chq_score.get_score(self.github_username)
                    self.github_updated = timezone.now()
                    
                    # get score
            else:
                # first time get score
                self.github_score = chq_score.get_score(self.github_username)
                self.github_updated = timezone.now()
        super(User, self).save(*args, **kwargs)