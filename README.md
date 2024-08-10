# One Page Podcast

You want to host your own Podcast.  You don't need anything else.

## Status

Minimally complete solution for serving a Podcast page.


## Clean Architecture

The code follows basic principles of [Clean Architecture](https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/), as outlined by Bob Martin, so that it is easy to understand and extend, and the central functions can be maintained independently from the environment.

### Layres

- opp.podcast describes the core entities
- opp.administrator and opp.visitor provide interface adaptors for the primary use-cases. Because it's just a basic podcast with little more than CRUD use-cases, there is not a separate layer of "business rules," although it would be simple to create one if needed. Abstract interfaces in this layer provide a dependency inversion for data storage interface adapters.
- opp.datastore contains an interface adapter for basic data storage.
- opp.web, opp.cli, and opp.config comprise components of the outermost framework / driver layer.  Of note, both the Flask web interface and the cli rely on the use cases and framework adapters to execute use-case functions; they do not have access or cause dependencies for those layers. In effect they are plug-ins for the core application.
