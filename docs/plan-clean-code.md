# Clean Architecture Remix

## TODO:

As admin, I want to create Episodes by uploading a file, with automatic extraction of available information.
- Admin "parse audio file" accepts a file handle
    - produces dict of
        - audio format
        - duration
        - (optional) title
        - (optional) description

- Admin interface "create episode"
    - accepts file handle & all arguments except guid
    - creates the guid
    - uses datastore interface to save data
    - returns a guid upon success

- Use a configuration file / interface
    - Hash password with python 'scrypt' library.
- Admin "create episode" as a user story
    - admin interface has an "extract details" function 

## Core Entities
podcast.py
    - SRP: only change when the definition of a podcast changes
    - data types for
        - channel
        - episode
        - ...

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
