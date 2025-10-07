# Code Review Guidelines

*Code review* is the process of a person examining changes to code;
often changes to code that they didn't make themselves.[^1]
Code review helps us improve code quality and helps us share knowledge.
Whilst code review isn't tied to [a particular pattern for managing code][1],
it's often associated with [GitHub flow][] and, consequently, pull requests (PRs).

Some guidelines for code review follow.

Ethelred has adopted the [Ship / Show / Ask][] branching strategy
([DR013](decision_records.md#013-adopt-ship--show--ask)).
By creating a pull request,
you're either showing (post-merge review) or asking (pre-merge review).
Please indicate which!

Try [asking like a DEAR][]:

* Describe the request
* Express how you feel about it
* Ask for specific feedback
* Reinforce kindness with gratitude and responsiveness

Try [reviewing to GIVE][]:

* Gentle
* Interested
* Validate
* Easy manner

[Google's Code Review Guidelines][] contains detailed guidance
for the person asking and for the person reviewing.

[^1]: The definition comes from [Google's Code Review Guidelines][].

[1]: https://martinfowler.com/articles/branching-patterns.html
[Asking like a DEAR]: https://developer-success-lab.gitbook.io/code-review-anxiety-workbook-1/part-two-managing-code-review-anxiety/step-4-proactively-engage/asking-like-a-dear
[GitHub Flow]: https://docs.github.com/en/get-started/using-github/github-flow
[Google's Code Review Guidelines]: https://google.github.io/eng-practices/review/
[Reviewing to GIVE]: https://developer-success-lab.gitbook.io/code-review-anxiety-workbook-1/part-two-managing-code-review-anxiety/step-4-proactively-engage/reviewing-to-give
[Ship / Show / Ask]: https://martinfowler.com/articles/ship-show-ask.html
