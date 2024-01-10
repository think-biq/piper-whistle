# piper-whistle

Tool to manage voices used with the [piper][1] speech synthesizer. You may also browse the [docs online][2] at https://think-biq.gitlab.io/piper-whistle/
There is also [a quick guide](https://hackernoon.com/how-to-set-up-piper-speech-synthesizer-on-a-local-machine) on how to setup and use piper and (piper-)whistle.

## usage

```bash
usage: piper_whistle [-h] [-d] [-v] [-V] [-P DATA_ROOT] [-R]
                     {guess,path,speak,list,preview,install,remove} ...

positional arguments:
  {guess,path,speak,list,preview,install,remove}

options:
  -h, --help            Show help message.
  -d, --debug           Activate very verbose logging.
  -v, --verbose         Activate verbose logging.
  -V, --version         Show version number.
  -P DATA_ROOT, --data-root DATA_ROOT
                        Root path where whistle should store config and data in.
  -R, --refresh         Refreshes (or sets up) language index by downloading the latest lookup.
```

## commands

### guess

```bash
usage: piper_whistle guess [-h] [-v] language_name

positional arguments:
  language_name  A string representing a language name (or code).

options:
  -h, --help     Show help message.
  -v, --verbose  Activate verbose logging.
```

Tries to guess the language you are looking for (and is supported by [piper][1]) from the name you provide.

### path

```bash
usage: piper_whistle path [-h] [-v] voice_selector

positional arguments:
  voice_selector  Selector of voice to search.

options:
  -h, --help      show this help message and exit
  -v, --verbose   Activate verbose logging.
```

Shows the local path to a specific model. The voice_selector has the format:
```
${CODE}:${NAME}@${QUALITY}/${SPEAKER}
```
The ```${SPEAKER}``` part is optional; as is the ```${CODE}``` part. So if you want to select the voice named 'alba' in quality 'medium', you could simply query: ```alba@medium```

The language code is infered.
Alternatively, you can just query with the model name listed by the `list` command.  
```
${CODE}-${NAME}-${QUALITY}
```
So for the example above, that would be ```en_GB-alba-medium```

### speak

```bash
usage: piper_whistle speak [-h] [-c CHANNEL] [-j] [-r] [-o OUTPUT] [-v] something

positional arguments:
  something             Something to speak.

options:
  -h, --help            Show help message.
  -c CHANNEL, --channel CHANNEL
                        Path to channel (named pipe (aka. fifo)) to which piper is listening.
  -j, --json            Encode the text as json payload. Is on by default.
  -r, --raw             Encode the text directly.
  -o OUTPUT, --output OUTPUT
                        Instead of streaming to audio channel, specifies a path to wav file where speech will be store in.
  -v, --verbose         Activate verbose logging.
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
* tty1: /opt/wind/piper/piper -m $(piper_whistle path alba@medium) --debug --json-input --output_raw < /opt/wind/channels/input > /opt/wind/channels/output
* tty2: aplay --buffer-size=777 -r 22050 -f S16_LE -t raw < channels/output

The tail command makes sure, that the payload on speak is send to input,
thereby keeping the file open after processing. Otherwise, the setup would exit
after [piper][1] has finished the first payload. This way you can continually prompt.

### list

```bash
usage: piper_whistle guess [-h] [-v] language_name

positional arguments:
  language_name  A string representing a language name (or code).

options:
  -h, --help     Show help message.
  -v, --verbose  Activate verbose logging.
```

This command lets you investigate available voices for specific languages, or
simply list all available voices. Using the --installed switch, you can filter
voices that are currently installed in the local cache directory. The cache is
located in the user app path, as provided by [userpaths](https://pypi.org/project/userpaths/) pip package. On linux this would be `${HOME}/.config/piper-whistle`. You may also get the model path on the remote host using -U.

### preview

```bash
usage: piper_whistle guess [-h] [-v] language_name

positional arguments:
  language_name  A string representing a language name (or code).

options:
  -h, --help     Show help message.
  -v, --verbose  Activate verbose logging.
```

With `preview`, you can download and play samples audio files, for any voice
supported by [piper][1]. It currently uses [mplayer](http://www.mplayerhq.hu/) to play the audio file.

### install

```bash
usage: piper_whistle guess [-h] [-v] language_name

positional arguments:
  language_name  A string representing a language name (or code).

options:
  -h, --help     Show help message.
  -v, --verbose  Activate verbose logging.
```

With `install` you can fetch available voice models and store them locally for
use with [piper][1]. You may first want to search for a voice you like with `list`
and then note the language code and index, so install knows where to look.
The model file (onnx) as well as its accompanying config (json) file, will be
stored in the local user data path as provide by [userpaths](https://pypi.org/project/userpaths/). On linux this would be `${HOME}/.config/piper-whistle`.

### remove

```bash
usage: piper_whistle guess [-h] [-v] language_name

positional arguments:
  language_name  A string representing a language name (or code).

options:
  -h, --help     Show help message.
  -v, --verbose  Activate verbose logging.
```

Any installed voice model can be deleted, via `remove`. You may pass the model name or shorthand selector.

[1]: https://github.com/rhasspy/piper
[2]: https://think-biq.gitlab.io/piper-whistle/
