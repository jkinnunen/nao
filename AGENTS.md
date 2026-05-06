# AGENTS.md

## Project Context

This repository contains `Nao`, an NVDA add-on focused on advanced OCR workflows on Windows.
It is a global NVDA plugin, not a standalone Python application.

Key context derived from the local codebase and the NVDA add-on development model:

- NVDA add-ons extend the screen reader through Python modules loaded by NVDA.
- Two common extension points are `appModules` for app-specific behavior and `globalPlugins` for global behavior.
- This project implements its main functionality under `addon/globalPlugins/nao/`.
- The packaged output is a `.nvda-addon` archive generated with `scons`.
- Add-on metadata is maintained in `buildVars.py`, which feeds manifest generation during build.

## Repository Layout

- `addon/globalPlugins/nao/`: main plugin package.
- `addon/globalPlugins/nao/framework/`: internal OCR, storage, threading, speech, and helper modules.
- `addon/locale/`: translations.
- `addon/doc/`: localized documentation.
- `buildVars.py`: add-on metadata, Python source globs, i18n source list.
- `sconstruct`: build logic for manifest generation, translations, HTML docs, and `.nvda-addon` packaging.
- `addon/installTasks.py`: install-time tasks for NVDA.

## Runtime Model

- The add-on runs inside NVDA, so many imports such as `addonHandler`, `globalPluginHandler`, `api`, `gui`, `wx`, `contentRecog`, and similar are provided by NVDA itself.
- Do not treat this repository like a generic Python CLI or web project.
- Most runtime behavior cannot be executed correctly outside NVDA.
- Windows is the target platform. OCR features rely on Windows OCR and Windows-specific integrations.

## Python Dependencies

Dependencies installed from `requirements.txt` are only the development/build-side Python packages used outside NVDA:

- `scons`
- `markdown`
- `comtypes`

Notes:

- `comtypes` is imported by the Explorer integration helper.
- NVDA-provided modules are not expected to be installed from `pip`.
- `gettext` is an external prerequisite on Windows for translation/build workflows; it is not installed through `pip` here.

## Common Tasks

Create or refresh the virtual environment:

```bash
./activate.sh
```

On Windows CMD:

```bat
activate.bat
```

Build the add-on:

```bash
scons
```

If the virtual environment is active, the equivalent is:

```bash
python -m SCons
```

## Editing Guidance

- Prefer modifying `buildVars.py` instead of editing generated manifest files.
- Keep source files under `addon/globalPlugins/nao/` ASCII unless the file already requires UTF-8 text.
- Do not commit generated artifacts such as `.nvda-addon`, generated `.html`, `.mo`, `.pot`, or `.ini` files unless explicitly requested.
- Be careful with Windows-specific subprocess, COM, Outlook, Explorer, and OCR code paths.
- Preserve compatibility with the supported NVDA range declared in `buildVars.py`.

## Validation Guidance

- Static validation:
  - inspect imports and packaging paths
  - run `python -m compileall addon` only for syntax checks when useful
  - run `python -m SCons` to validate packaging
- Behavioral validation:
  - requires manual testing inside NVDA on Windows
  - especially for Explorer, Outlook, screenshot OCR, and localized/document-cache flows

## Source References

High-level NVDA add-on context for this file was aligned with:

- the local repository structure
- `readme.md`
- `buildVars.py`
- the article "Introduzione allo Sviluppo di Addon per NVDA" on `alessandroalbano.it`
