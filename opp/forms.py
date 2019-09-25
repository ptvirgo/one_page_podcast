from datetime import datetime
import io
import os
import pytz
import hashlib
import mutagen

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
import wtforms as form
from wtforms.ext.dateutil.fields import DateTimeField
import wtforms.validators as validator

from .models import Episode, AudioFile, AudioFormat, Keyword

class LoginForm(FlaskForm):
    """
    Provide a log in form
    """
    username = form.StringField(
        label="Username", validators=[validator.DataRequired()])
    password = form.PasswordField(
        label="Password", validators=[validator.DataRequired()])

    def __init__(self, expect_user, expect_pass, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Will likely want to work hashing into the OPP settings, but at least
        # keep these off anything exposed to front-end templates
        self._expect_user = hashlib.sha256(expect_user.encode()).hexdigest()
        self._expect_pass = hashlib.sha256(expect_pass.encode()).hexdigest()

    def validate_username(self, field):
        """Require the correct username"""
        username = hashlib.sha256(field.data.encode()).hexdigest()
        if username != self._expect_user:
            raise validator.ValidationError("Invalid credentials")

    def validate_password(self, field):
        """Require the correct password"""
        password = hashlib.sha256(field.data.encode()).hexdigest()
        if password != self._expect_pass:
            raise validator.ValidationError("Invalid credentials")


class CreateEpisodeForm(FlaskForm):
    """
    Provide a form for creating episodes
    """
    title = form.StringField(
        label="Title", validators=[validator.DataRequired()])
    published = DateTimeField(
        label="Publication date & time", validators=[validator.DataRequired()])
    description = form.StringField(
        label="Description", validators=[validator.DataRequired()])
    explicit = form.BooleanField(
        label="Explicit", false_values=("false", "False", ""))
    keywords = form.StringField(
        label="Keywords", validators=[validator.Optional()])
    audio_file = FileField(
        label="Audio file", validators=[FileRequired()])

    def __init__(self, media_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.media_dir = media_dir

    def create_episode(self):
        """Produce the episode described by the form fields"""
        af_data = self.audio_file.data.read()
        af = mutagen.File(io.BytesIO(af_data))

        try:
            af_format = AudioFormat[af.__class__.__name__]
        except KeyError:
            msg = "Invalid audio format: use one of %s" % (
                ", ".join([x.value for x in AudioFormat]))
            return msg, 400

        af_name = AudioFile.standardized_name(
            self.published.data, self.title.data, af_format)

        af_path = os.path.join(self.media_dir, af_name)

        with open(af_path, "wb") as f:
            f.write(af_data)

        episode = Episode(
            title=self.title.data,
            published=self.published.data,
            description=self.description.data,
            explicit=self.explicit.data)

        audio_file = AudioFile(
            file_name=af_name,
            audio_format=af_format,
            length=os.path.getsize(af_path),
            duration=round(af.info.length))

        episode.audio_file = audio_file

        if self.keywords.data is not None:
            words = self.keywords.data.split(",")
            episode.set_keywords(words)

        return episode


class UpdateEpisodeForm(FlaskForm):
    """
    Provide a form for updating episodes
    """
    title = form.StringField(
        label="Title", validators=[validator.Optional()])
    published = DateTimeField(
        label="Publication date & time", validators=[validator.Optional()])
    description = form.StringField(
        label="Description", validators=[validator.Optional()])
    explicit = form.BooleanField(
        label="Explicit", false_values=("false", "False", ""))
    keywords = form.StringField(
        label="Keywords", validators=[validator.Optional()])

    def __init__(self, time_zone, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_zone = time_zone
    
    def update_episode(self, episode):
        """Update the given episode"""
        if self.title.data is not None and self.title.data != "":
            episode.title = self.title.data

        if self.description.data is not None and self.description.data != "":
            episode.description = self.description.data

        # wtforms does not support empty boolean fields, we have to assume the
        # correct setting
        episode.explicit = self.explicit.data

        if self.published.data is not None:
            episode.published = self.published.data

        if self.keywords.data is not None and self.keywords.data != "":
            words = self.keywords.data.split(",")
            episode.set_keywords(words)

        return episode


class DeleteEpisodeForm(FlaskForm):
    """
    Provide a form to confirm deleting an episode
    """
    confirm = form.BooleanField(
        label="Are you sure you want to delete this episode?",
        false_values=("false", "False", ""))

    def validate_confirm(self, field):
        if not field.data:
            raise validator.ValidationError("Not confirmed")
