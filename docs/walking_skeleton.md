# Walking Skeleton

## What is a walking skeleton?

> A walking skeleton is a tiny implementation of the system that performs a small end-to-end function.
> It need not use the final architecture,
> but it should link together the main architectural components.
> The architecture and the functionality can then evolve in parallel.
>
> [Crystal Clear: A Human-Powered Methodology for Small Teams][], by Alistair Cockburn

Cockburn emphasises that a walking skeleton is permanent code;
once the system is up and running, it should stay up and running.

> A walking skeleton is an implementation of the thinnest possible slice of real functionality that we can automatically build, deploy, and test end-to-end.
> It should include just enough of the automation, the major components, and communication mechanisms to allow us to start working on the first feature.
>
> [Growing Object-Oriented Software, Guided by Tests][], by Steve Freeman and Nat Pryce

Citing Cockburn, Freeman and Pryce include communication mechanisms in their definition of a walking skeleton.

## What is Ethelred's walking skeleton?

We explored job requests, jobs, and workflow runs in response to an early [motivating question][1].
Since then, however, a *real user* has expressed a *real need* to understand logins to our various platforms!

We will start with logins to OpenCodelists.

* On a schedule;
* obtain a new copy of the OpenCodelists database;
* extract new logins from it;
* append them to an existing datastore;
* present the number of logins per day on a timeseries.

The above should be [deployed](deployment.md) and tested end-to-end.

[1]: https://docs.google.com/document/d/1C1ZCiYZMAwHMd7PwIWmcU-yYu_IcMpvoS4IOkq5EjFI/edit?tab=t.0#heading=h.z2hfz8bzxxh6
[Crystal Clear: A Human-Powered Methodology for Small Teams]: https://learning.oreilly.com/library/view/crystal-clear-a/0201699478/
[Growing Object-Oriented Software, Guided by Tests]: https://learning.oreilly.com/library/view/growing-object-oriented-software/9780321574442/
