# terminal_recorder

A small tool to record a terminal session to be played back later.

## Build terminal_recorder

```
chmod +x compile.sh
./compile.sh
```

## Install python requirements for log_playback.py

```
python install -r requirements.txt
```

## How to use

Launch `./terminal_recorder` and perform some random actions which will be recorded into terminal_log.bin placed in the same directory.
Then run `python3 log_playback.py ./terminal_log.bin` to replay the recording.
Make sure you have all the necessary python dependencies installed in your environment.
