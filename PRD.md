**Image Card Generator Streamlit Application**

**1. Introduction**

**1.1 Purpose**
This document defines the Product Requirements (PRD) and Minimum Viable Product (MVP) scope for a Streamlit-based Image Card Generator that leverages the OpenAI Image API for generative and edit workflows. It will guide design, development, and launch.

**1.2 Scope**

* Users can enter a text prompt and optionally upload one or more reference images.
* The app will call OpenAI’s Image API to generate 4–5 image options per prompt.
* Generated images are displayed in a grid for selection and optional in‐app editing.
* Initial launch focuses on core generation and download; future releases will add mask-based inpainting and parameter controls.

---

**2. Objectives & Goals**

* **Speed**: Generate and display image cards within 30 seconds.
* **Simplicity**: Intuitive UI for non-technical users.
* **Quality**: Leverage `gpt-image-1` (or DALL·E 3 for higher fidelity) for high-quality outputs.
* **Extensibility**: Modular code for easy addition of editing, variation, and parameter tuning.

---

**3. Stakeholders**

* **End Users**: Designers, marketers, content creators wanting quick visual assets.
* **Product Manager**: Defines roadmap and success metrics.
* **Developers**: Implement Streamlit front-end and OpenAI integrations.
* **UX/Design**: Craft interface and user experience flows.
* **DevOps/Security**: Manage deployment, API keys, and compliance.

---

**4. User Stories**

1. As a user, I want to input a text prompt and optionally upload reference images so that the app can generate tailored visuals.
2. As a user, I want to see multiple image options at once so I can choose my favorite.
3. As a user, I want to download any generated image to my local machine.
4. (Future) As a user, I want to apply mask-based edits to refine parts of an image.
5. (Future) As a user, I want to adjust generation parameters (size, quality, background, format) before generating.

---

**5. Functional Requirements**

| ID  | Requirement                                                                     |
| --- | ------------------------------------------------------------------------------- |
| FR1 | Text input field for prompt (multiline).                                        |
| FR2 | File uploader supporting 1–4 reference images (PNG/JPEG).                       |
| FR3 | "Generate" button triggers OpenAI Image API call with `n=4`.                    |
| FR4 | Display returned images in a 2×2 grid with download buttons.                    |
| FR5 | Allow user to select an image to open an "Edit" panel.                          |
| FR6 | In MVP: Edit panel only allows re-prompt and regenerate selection.              |
| FR7 | Error handling: display friendly messages on API/timeouts/invalid inputs.       |
| FR8 | Secure storage of API key in environment variable; never exposed in UI or logs. |

---

**6. Non-functional Requirements**

* **Performance**: API response ≤30 s; UI render ≤2 s.
* **Scalability**: Stateless Streamlit instance; scale horizontally on cloud.
* **Security**: HTTPS; OpenAI key stored in `OPENAI_API_KEY`.
* **Usability**: Responsive layout for desktop and tablet.
* **Maintainability**: Clear modular code, unit tests for API wrapper.

---

**7. Success Metrics**

* **Adoption**: 500 unique users in first month.
* **Engagement**: Average of ≥3 generations per session.
* **Performance**: 95% of requests complete within 30 s.
* **Retention**: 40% of users return within two weeks.

---

**8. Technical Architecture**

1. **Front-end**: Streamlit app (`app.py`) with sections: prompt input, uploader, gallery, edit panel.
2. **API Layer**: Python wrapper for OpenAI Image endpoints (`generate()`, `edit()`, `variations()`).
3. **State Management**: `st.session_state` to store prompts, uploaded images, API responses.
4. **Hosting**: Deploy to Streamlit Cloud or Docker container on AWS/GCP.
5. **Logging & Monitoring**: Integrate Sentry for error tracking; use built-in metrics for response times.

---

**9. MVP Scope**

* **Core**: Text-only prompt → 4-image generation → display + download.
* **Optional**: Reference image upload for "style guess" → incorporate in generation call.
* **Excluded**: Mask-based inpainting, parameter sliders, user accounts, history.

---

**10. Future Roadmap**

* **v1.1**: Add inpainting support via mask upload.<br>**v1.2**: Parameter panel for size/quality/format/background.<br>**v1.3**: User authentication & saved projects.<br>**v1.4**: Variation endpoint integration for DALL·E 2.

---

**11. Implementation Plan & Timeline**

1. **Week 1**: Prototype UI in Streamlit (inputs + grid).<br>2. **Week 2**: Integrate OpenAI generate API; handle base64 decoding & display.<br>3. **Week 3**: Add file uploader support; pass reference images to the API.<br>4. **Week 4**: QA and performance tuning; prepare deployment pipeline.<br>5. **Week 5**: Beta launch & gather feedback.

---

**12. Risks & Mitigations**

* **API Rate Limits**: Monitor usage; implement retries/backoff.<br>**Mitigation**: Expose error to user and suggest retry.
* **High Latency**: Complex prompts may delay.<br>**Mitigation**: Show loading spinner; allow medium quality fallback.
* **Cost Overrun**: Uncontrolled usage could spike costs.<br>**Mitigation**: Enforce usage quotas or warnings.

---

*End of PRD & MVP Document*
