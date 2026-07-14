# Phase G03 Release Verification

**Date:** 2026-07-14  
**Verdict:** **FAIL — release baseline is not yet committed**

## 1. Repository commit baseline

- Candidate committed baseline: `7a2f02dcf4534ae1f1b255de13e8632998c267fd`
- Subject: `phase-acl03: constrain sales manager projection editing`
- Clean detached snapshot: `C:\tmp\espocrm-production-g03-release-7a2f02d`

## 2. Version verification

The committed candidate's `crm-extension/manifest.json` declares `1.9.0-alpha`.
The working-tree `1.9.5-alpha` manifest update and its extension skeleton assertions are staged but not committed. Consequently, a `v1.9.5-alpha` tag cannot truthfully target the committed candidate.

## 3. Release artifact and checksum

Existing untracked files are present at:

- `deployment/prospecting-extension-1.9.5-alpha.zip`
- `deployment/prospecting-extension-1.9.5-alpha.zip.sha256`

They were not regenerated or overwritten because the committed source baseline does not declare `1.9.5-alpha`.

## 4. Git tag information

No `v1.9.5-alpha` tag was created. Creating it at the current committed baseline would misrepresent the package version.

## 5. Clean working tree verification

The detached snapshot for commit `7a2f02d` was clean. The primary workspace is not clean: it contains staged Docs/Test artifacts, historical package relocation changes, archive backups, and an untracked C11 audit document.

## 6. Regression Gate result

Not run. The requested clean post-commit `1.9.5-alpha` baseline does not exist.

## 7. Required release prerequisite

Commit an agreed `1.9.5-alpha` release baseline (including the manifest and matching test expectation), then run the artifact build, checksum verification, tag creation, and full Regression Gate from that clean commit.

## 8. Boundary confirmation

No C11 changes were created or staged by this verification attempt. No C09, C10, C10.6, ACL03, business code, or test logic was modified.
