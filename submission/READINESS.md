# Submission checklist — 8 November 2026

## Submission artifacts

- [x] Devpost copy covers required fields, Track 2, Panos Georgakopoulos and Apostolos Dedeloudis.
- [x] Final deck: `DECOUPLE_Submission_Visual.pptx`, 10 slides, all light mode.
- [x] Final pitch: `video_production/output/DECOUPLE_Pitch_captioned.mp4`, 8:14, 1080p; optional plain MP4 and SRT.
- [x] Apostolos's newer UI redesign incorporated locally. The approved recorded layout predates it; disclosed in RELEASE_NOTES.md.
- [x] README covers installation, offline replay, full data download, benchmark reproduction, method distinctions and limitations.
- [x] Data/font/media attribution in THIRD_PARTY_NOTICES.md.
- [x] Sensitive/generated/legacy files excluded from the planned source package.

## Before pressing Submit

- [x] Public `main` contains the tested submission and Apostolos’s redesign; earlier histories and branches preserved.
- [x] Final deck, MP4s, SRT and chapters published in [submission release](https://github.com/panosgeorgakopoulos/Ethnohack/releases/tag/submission-2026-11-08). Anonymous deck and captioned-video downloads matched local files byte for byte.
- [ ] Upload the pitch to a Devpost-supported video host and paste the player URL. A GitHub downloadable MP4 may not satisfy Devpost's embedded-video field.
- [x] Team confirmed a three-month ElevenLabs student plan; narration credited in the publication notes. Approved video unchanged.
- [ ] Add both members to Devpost, attach the deck and repository, and submit before the event's actual deadline.

## Verification status

See DELIVERY.md for media checks and RELEASE_NOTES.md for source changes. 52 local tests passed; a fresh environment installed successfully and the clean offline source passed 37 tests (15 expected raw-data skips). Fixture integrity and benchmark smoke checks passed. Hosted CI and publication are tracked above.
