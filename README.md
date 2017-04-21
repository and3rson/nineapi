=====
Index
=====

Documentation is here: https://nineapi.readthedocs.org

So I'm sick and tired with web apps. I want normal adequate desktop apps for all the things.

Same relates to 9GAG. Everyone says there's no official API for 9GAG, but of course there is - you just need to go deeper.

Here's what I did in 20 minutes:

- Decompiling 9GAG app for Android and digging within its JS sources (that's right - JavaScript, not Java: 9GAG app seems to be written in React Native.) to find the logic for signing requests.
- Dumping HTTP traffic with spoofed SSL certificates to see actual request & response bodies.

So far there seem to be multiple domains used including `api.9gag.com`, `ad.9gag.com`, `notify.9gag.com`, `admin.9gag.com` and `comment-cdn.9gag.com`. I was able to make my own requests and retrieve the data I want.

Any fellow coders willing to contribute to this? We would be the first ones to reverse-engineer an actual 9GAG API. How cool is that?

