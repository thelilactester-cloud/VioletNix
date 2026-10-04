# Background music

Drop royalty-free tracks here (`.mp3`, `.wav`, `.m4a`, `.ogg`). The pipeline picks one at random per
video, loops it and lowers it under the narration.

**Only use tracks you are allowed to use commercially.** Good free sources:
- YouTube Audio Library (studio.youtube.com → Audio Library): filter by "no attribution required"
- Pixabay Music (pixabay.com/music): free for commercial use
- Free Music Archive (check each track's licence)

Dark, cinematic and ambient tracks suit history storytelling. Keep the licence/attribution note for
each track in a `LICENSES.md` file next to them.

**Do not put chart songs or other people's copyrighted music here.** YouTube and Facebook will claim
or mute the video. For TikTok trending sounds, use the draft workflow described in `pipeline/README.md`.

## Licence gate (required)
The pipeline **only uses tracks listed by file name in `music/LICENSES.md`**. For each track add a line:

```
my-track.mp3 | Pixabay Music | https://pixabay.com/music/... | Pixabay Content Licence, no attribution required
```
An unlisted track is skipped. This keeps uncleared music out of videos, which is the most common way
channels get claims and lose monetization.
