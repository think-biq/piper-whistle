# piper-whistle

Tool to manage voices used with the piper speech synthesizer.

## usage

```bash
whistle [-h] [-v] [-V] [-R] {guess,path,speak,list,preview,install}

positional arguments:
  {guess,path,speak,list,preview,install}

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Activate verbose logging.
  -V, --version         Show version number.
  -R, --refresh         Refreshes (or sets up) language index by downloading the latest lookup.
```

## commands

### guess

Tries to guess the language you are looking for (and is supported by piper) from the name you provide.

```bash
whistle guess [-h] language_name

positional arguments:
  language_name  A string representing a language name (or code).

optional arguments:
  -h, --help     show this help message and exit
```

### path

```bash
whistle path [-h] voice_selector

positional arguments:
  voice_selector  Selector of voice to search.

optional arguments:
  -h, --help      show this help message and exit
```

### speak

```bash
whistle speak [-h] something

positional arguments:
  something   Something to speak.

optional arguments:
  -h, --help  show this help message and exit
```

### list

```bash
whistle list [-h] [-I] [-a] [-L] [-p] [-l LANGUAGE_CODE] [-i VOICE_INDEX]

optional arguments:
  -h, --help            show this help message and exit
  -I, --installed       Only list installed voices.
  -a, --all             List voices for all available languages.
  -L, --languages       List available languages.
  -p, --install-path    List path of voice (if installed).
  -l LANGUAGE_CODE, --language-code LANGUAGE_CODE
                        Only list voices matching this language.
  -i VOICE_INDEX, --voice-index VOICE_INDEX
                        List only specific language voice.
```

### preview

```bash
whistle preview [-h] [-l LANGUAGE_CODE] [-i VOICE_INDEX] [-s SPEAKER_INDEX]
                       [-D]

optional arguments:
  -h, --help            show this help message and exit
  -l LANGUAGE_CODE, --language-code LANGUAGE_CODE
                        Select language.
  -i VOICE_INDEX, --voice-index VOICE_INDEX
                        Specific language voice. (defaults to first one)
  -s SPEAKER_INDEX, --speaker-index SPEAKER_INDEX
                        Specific language voice speaker. (defaults to first one)
  -D, --dry-run         Build URL and simulate download.
```

### install

```bash
whistle install [-h] [-D] language_code voice_index

positional arguments:
  language_code  Select language.
  voice_index    Specific language voice. (defaults to first one)

optional arguments:
  -h, --help     show this help message and exit
  -D, --dry-run  Simulate download / install.
```