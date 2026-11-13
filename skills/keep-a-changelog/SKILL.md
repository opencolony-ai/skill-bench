---
name: keep-a-changelog
description: Update CHANGELOG.md for merged pull requests in this repository's format. Use whenever you add entries to a changelog.
---
# Changelog entries

- Add entries only under `## [Unreleased]`. If it is missing, create it directly above the
  first released version heading. Never edit a released version's section.
- Sections, in this order and only when they have entries:
  `### Added`, `### Changed`, `### Deprecated`, `### Removed`, `### Fixed`, `### Security`.
- Labels to sections: feature -> Added, enhancement -> Changed, deprecation -> Deprecated,
  removal -> Removed, bug -> Fixed, security -> Security. With several labels, the first that
  applies in this order wins: security, removal, deprecation, bug, feature, enhancement.
- Pull requests labelled `internal`, `ci` or `docs` are not listed.
- Entry: `- <title, without a trailing period> ([#<n>](https://github.com/acme/shop/pull/<n>))`
- Keep entries already under Unreleased. Within a section, order entries by PR number, ascending.
