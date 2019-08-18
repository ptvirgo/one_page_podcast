# One Page Podcast

Develop an app allowing podcast authors to easily self-host their content.

Ideally:
    - One-click install
    - One-click uploads
    - Stand-alone app, assumes you do not want or need additional content on the same subdomain.


## References:

https://www.thepolyglotdeveloper.com/2016/02/create-podcast-xml-feed-publishing-itunes/

## Site-wide Data
- title
- subtitle
- description
- image
- link (to home page)

- author
- email
- location

- language
- eplicit
- rating
- keywords
- category
- frequency


## Per-episode data, for the database

- title
- link (to the file)
- pubDate
- description
- length (bytes)
- format ("audio/mpeg" or  ...?)
- itunes:duration (mm:ss)
- itunes:image (link to image, appears optional)
- itunes:keywords
- itunes:explicit (yes or no)

## rss
- guid (apparently same as the link to the file)
- itunes:summary (description)


## Database Tables

### episodes

- id
- title
- published (date)
- updated (date)
- description
- image (optional file)
- explicit (bool)


### files
- id
- link
- format
- length (bytes)
- duration (mm:ss)
- episode (foriegn key to episode id)

### episode_keywords
- episode (fk)
- keyword (fk)

### keywords
- id
- keyword
