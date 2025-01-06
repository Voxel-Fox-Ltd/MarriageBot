# Styleguide

Just some bulletpoints so that anyone contributing can be consistent with both the code and the outputs.

## Code

### Modules

* All modules be in order:
    * A copyright notice
    * Relevant imports
    * `if TYPE_CHECKING` block
    * `__all__` block
    * Any global-scope variables
    * Main body classes/functions
* Translator notes:
    * Translator notes are only required when additional context is necessary.
    * Generally, additional context will always be needed for command and option names.

## Outputs

* All visible outputs should be given as embeds.
* Ephemeral outputs should generally be non-embedded.
* Anything posted publically should be translated to the language of the guild.
* Ephemeral ouptuts can be translated either way.
