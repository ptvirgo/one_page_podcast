# One Page Podcast

You want to host your own Podcast.  You don't need anything else.

The goal is to prepare a solution that is simple and effective for people who
are technically savvy, while minimizing the actual effort required to get up
and running.

## Status

Minimally complete solution for serving a Podcast page.  


## Templates

It should be easy to make new OPP templates with a basic knowledge of HTML, CSS
and [Jinja templates](https://jinja.palletsprojects.com/).

### Directory structure

A new template must be stored in the site-wide template directory. As a Flask
app, OPP expects templates and related static content to be in separate
directories, as follows.

- templates/
    - admin/\* *# admin templates, required and not to be altered*
    - your_template/index.html *# A jinja template that will render the front page*
- static/
    - admin/\* *# admin static files, required and not to be altered*
    - your_template/\* *# any css, image, or js files you wish to include*

This structure will allow an OPP admin to activate your template simply by
storing the associated files and setting their *template name* setting to
*your_template.*


### Tags

OPP delivers the following tags to the template.

- **podcast** # Details about the podcast
    - **title**
    - **subtitle**
    - **description**
    - **image** # A file-name for the podcast's main image.  For the url, use `{{ url_for('media', filename=podcast.image) }}`
    - **link** # URL for the podcast, as expected by the rss template
    - **author** # The podcast author's name
    - **email** # The podcast author's contact email
    - **language** # Language code, likely "en"
    - **explicit** # Boolean
    - **keywords** # A list of keywords for the podcast.
    - **category** # The podcast category

- **episodes** is a list of:
    - **title**
    - **description**
    - **image** # optional image filename, typical use: `{{ url_for('media', filename=episode.image) }}`
    - **keywords** # Keywords - comma separated: `{{ episode.keywords|episode_keywords }}` or access the `word` attribute of each.
    - **published** # publication date.  Typical formatting `{{ episode.published|datetime }}`
    - **explicit** # Boolean
    - **audio_file** # data about the audio file, contains:
        - **duration** # Duration in seconds.  Translate to hours, minutes, seconds via `{{ episode.audio_file.duration|duration }}`
        - **filename** # For the url: `{{ url_for('media', filename=episode.audio_file.file_name, _external=True) }}`
        - **mimetype** # The mimetype, as needed for inline playback
