## Justice Transcribe Roadmap

### Help Page (v1 → v1.1)

Goals
- Provide self‑serve resources and an entry point to restart onboarding.
- Reduce support requests by making guidance easily discoverable.

Scope (existing prototype)
- Placeholder Tutorial Video tile with CTA.
- Interactive Tutorial tile to redo onboarding.
- Link block to Microsoft Teams support channel.
- Link block to AI Policies & Guidelines.
- Link block to Probation Information Flyer download.

UI/UX Improvements from screenshot review
- Hierarchy and spacing
  - Increase vertical spacing between major sections to improve scanability.
  - Use consistent card heights for the two top tiles (Tutorial Video, Interactive Tutorial).
  - Add subtle section dividers or headings for "Get Started", "Support", and "Policies".
- Card CTAs
  - Elevate primary CTAs ("Play Tutorial", "Restart Tutorial") with a stronger fill style and clear icons.
  - Add secondary link styles inside cards for additional context where needed.
- States & placeholders
  - For "Coming soon" tutorial video, include an email notify toggle or link to updates; add disabled hover state.
  - Show loading/empty/error states for links (Teams/Policy/Flyer) if the endpoints fail.
- Icons & affordance
  - Replace generic circular icons with purposeful icons (play, refresh, shield, document, team).
  - Ensure all clickable areas have hover/active/focus states and accessible hit areas.
- Accessibility
  - Ensure color contrast WCAG AA for text and buttons.
  - Provide aria-labels for CTAs and descriptive alt text for icons.
  - Keyboard navigation order should follow visual flow; visible focus rings on interactive elements.
- Content
  - Add one-line descriptions under each card to clarify value (e.g., "Short video: how to record, label speakers, generate minutes").
  - Standardize microcopy tone and punctuation; correct spelling for "Interactive Tutorial" and "information".
- Navigation & breadcrumbs
  - Keep breadcrumb (Home > Help) but ensure the back affordance is consistent with app-wide pattern.
- Performance
  - Lazy-load video assets; avoid blocking render.
- Analytics
  - Track clicks on each card/CTA; log completion of interactive tutorial restarts.

Acceptance Criteria (Help v1.1)
- Consistent card layout and spacing across all screen sizes.
- Primary CTAs have clear focus/hover/active states and pass a11y checks.
- "Coming soon" video shows disabled state with option to get notified.
- Links validated: Teams, Policies, Flyer open correctly (new tab for external).
- Analytics events: help_view, help_play_tutorial_click, help_restart_tutorial_click, help_teams_click, help_policies_click, help_flyer_click.

Technical Notes
- Create `app/help/page.tsx` if not already; compose from reusable `Card` component.
- Centralize external URLs in a config file to avoid duplication.
- Tutorial video asset will be stored in Sanity.io. Query via GROQ using the Sanity client, and render through a responsive player. Add a safe fallback if the asset is unpublished/unavailable.
- Add PostHog events for the above analytics.

Open Questions
- Should the Teams link be tenant-specific or environment-configured?

---

### Onboarding Flow (v1)

Goals
- Guide first-time users through permissions, audio setup, speaker labeling, and generating minutes.
- Make it repeatable and accessible from Help page.
- Ensure consistent brand/layout with the same-sized logo in the top-right throughout the flow.

Detailed Steps (7 screenshots; align with `@onboarding flow/` design files)
1. Welcome
   - Brief intro and privacy summary; CTA: "Continue" (disabled until user acknowledges privacy blurb).
2. Let's get you set up
   - Inputs: email address; numeric input: "How long do you spend writing CRISSA notes (minutes)?".
   - Validation: email must be valid format; minutes must be a positive integer.
   - The black "Continue" button is hidden/disabled until both inputs are valid; then appears/enables.
3. Recording sessions
   - Overview of recording options; placeholder for a short video (hosted in Sanity.io).
   - Secondary links to Help page sections for recording tips.
4. Permissions check
   - Microphone and system audio permissions helpers with inline troubleshooting.
   - Show real-time permission state; allow re-check.
5. Speaker labeling primer
   - Short explanation with example of labeling speakers prior to minutes.
6. Email notifications
   - Confirm the email captured in Step 2 and display it prominently; allow edit inline.
   - Explain what notifications are sent (e.g., transcript ready, minutes ready).
7. You're ready
   - Primary CTA: "Start first recording" → navigates to Home screen.
   - Link: "Need help? Visit support" → navigates to Help page.

Key Requirements
- Global layout: keep the same-sized logo in the top-right across all steps.
- State & persistence: persist form values (email, minutes) and current step in local storage; allow restart from Help page.
- Step 2 validation: email valid; minutes > 0; only then the black Continue button appears/enables.
- Step 3 media: render video from Sanity if available; otherwise show placeholder and copy.
- Step 6 echo: show the exact email entered earlier; support edit with validation.
- Step 7 navigation: "Need help?" link opens Help; "Start first recording" routes to Home.
- Accessibility-first; keyboard-only completion possible; visible focus states; WCAG AA contrast.
- Allow cancel/resume; persist step state across reloads.
- Metrics: onboarding_start, onboarding_step_view(step_id), onboarding_step_continue(step_id), onboarding_complete, onboarding_restart.

Acceptance Criteria (Onboarding v1)
- The logo size and position remain visually identical across all seven steps.
- Step 2: Continue button remains hidden/disabled until both inputs pass validation; invalid inputs show inline messages.
- Step 3: Video renders from Sanity when published; if not available, a placeholder with helpful text is shown.
- Step 6: The email displayed matches the stored value from Step 2; editing updates the stored value.
- Step 7: "Need help? Visit support" routes to `/help`; "Start first recording" routes to the Home screen.
- On refresh, the user returns to the last completed step; Restart from Help clears progress if confirmed.

Dependencies
- Reuse components from `components/audio` and `components/minutes` where possible.
- Sanity.io client for fetching video content (recording sessions) and any future onboarding assets.

Technical Notes
- Implement as a wizard with controlled state; either a single `app/onboarding/page.tsx` with internal steps or routes like `app/onboarding/step-[1..7]`.
- Persist onboarding state to IndexedDB/localStorage; optional server persistence once user account exists.
- Use PostHog for analytics with the event names listed above.
- Add a helper in the Help page to trigger onboarding restart (clears stored state).

Next Actions
- Finalize content and assets for each step (copy, illustrations, Sanity video).
- Implement the wizard, validation, persistence, routing, and analytics.

