# piper-whistle

Tool to manage voices used with the [piper][1] speech synthesizer.

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

```bash
whistle guess [-h] language_name

positional arguments:
  language_name  A string representing a language name (or code).

optional arguments:
  -h, --help     show this help message and exit
```

Tries to guess the language you are looking for (and is supported by [piper][1]) from the name you provide.

### path

```bash
whistle path [-h] voice_selector

positional arguments:
  voice_selector  Selector of voice to search.

optional arguments:
  -h, --help      show this help message and exit
```

Shows the local path to a specific model. The voice_selector has the format:
```
${CODE}:${NAME}@${QUALITY}/${SPEAKER}
```
The ${SPEAKER} part is optional; as is the ${CODE} part. So if you want to select the voice named 'alba' in quality 'medium', you could simply query: ```alba@medium```

The language code is infered.
Alternatively, you can just query with the model name listed by the `list` command.  
```
${CODE}-${NAME}-${QUALITY}
```
So for the example above, that would be ```en_GB-alba-medium```

### speak

```bash
whistle speak [-h] something

positional arguments:
  something   Something to speak.

optional arguments:
  -h, --help  show this help message and exit
```

Currently only works on linux / bsd systems, with a FIFO (aka. named pipes) setup. The basic idea is, having one pipe accepting json input (provided by this command), which is listened to by [piper][1]. After [piper][1] has processed the audio, it is either saved to file or passed on to another FIFO, which can then be read by a streaming audio player like `aplay`.

Example:
Assuming [piper][1] is installed at /opt/wind/piper, the named pipes are located at /opt/wind/channels and whistle is available in $PATH, the aformentioned setup could look like the following:

pipes:

* /opt/wind/channeld/speak - accepts json payload
* /opt/wind/channeld/input - read by [piper][1]
* /opt/wind/channeld/ouput - written by [piper][1]

processes:

* tty0: tail -F /opt/wind/channels/speak | tee /opt/wind/channels/input
* tty1: /opt/wind/piper/piper -m $(whistle path alba@medium) --debug --json-input --output_raw < /opt/wind/channels/input > /opt/wind/channels/output
* tty2: aplay --buffer-size=777 -r 22050 -f S16_LE -t raw < channels/output

The tail command makes sure, that the payload on speak is send to input,
thereby keeping the file open after processing. Otherwise, the setup would exit
after [piper][1] has finished the first payload. This way you can continually prompt.

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

This command lets you investigate available voices for specific languages, or
simply list all available voices. Using the --installed switch, you can filter
voices that are currently installed in the local cache directory. The cache is
located in the user app path, as provided by [userpaths](https://pypi.org/project/userpaths/) pip package. On linux this would be `${HOME}/.config/piper-whistle`.

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

With `preview`, you can download and play samples audio files, for any voice
supported by [piper][1]. It currently uses [mplayer](http://www.mplayerhq.hu/) to play the audio file.

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

With `install` you can fetch available voice models and store them locally for
use with [piper][1]. You may first want to search for a voice you like with `list`
and then note the language code and index, so install knows where to look.
The model file (onnx) as well as its accompanying config (json) file, will be
stored in the local user data path as provide by [userpaths](https://pypi.org/project/userpaths/). On linux this would be `${HOME}/.config/piper-whistle`.

[1]: https://github.com/rhasspy/piper