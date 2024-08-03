# Clean Architecture Remix

## TODO:

1. Audio files are downloadable
2. RSS
3. HTML front end

### Web interface

Flask routes
- / : HTML, user friendly episode display
- /podcast.xml : rss
    - (maybe) episode keywords
    - add / improve [xml tags](https://github.com/Podcast-Standards-Project/PSP-1-Podcast-RSS-Specification?tab=readme-ov-file#required-channel-elements):
        - copyright
        - subtitle
- [Validate](https://podba.se/validate/)

- 'scrypt' library looks good for password hashing

## Core Entities
podcast.py
    - SRP: only change when the definition of a podcast changes

## Use cases (Business Rules)

Admin user: CRUD
- CRU channel
- CRUD episodes

Visitor: Read only
- get channel
- get episodes

Behind the interface boundary; should provide the class definition for an interface.


## Interfaces and Adapters

The software in the interface adapters layer is a set of adapters that convert data from the format most convenient for the use cases and entities, to the format most convenient for some external agency such as the database or the web.

> You might be tempted to have these data structures contain references to Entity objects. You might think this makes sense because the Entities and the request/response models share so much data. Avoid this temptation! The purpose of these two objects is very different. Over time they will change for very different reasons, so tying them together in any way violates the Common Closure and Single Responsibility Principles. (Clean Architecture, "Request and Response Models")

## Frameworks and Drivers

Flask & main, basically.
