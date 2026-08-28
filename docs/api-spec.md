# API v1

Base: `/api/v1`

## Auth
| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/otp/request` | Send OTP to mobile |
| POST | `/auth/otp/verify` | Verify OTP, issue JWT |
| GET  | `/auth/me` | Current user |

## Profile
| POST | `/profiles` | Create applicant profile |
| GET  | `/profiles/{id}` | Fetch profile |
| PATCH| `/profiles/{id}` | Update profile |

## Schemes
| GET  | `/schemes` | List / filter scheme catalogue |
| GET  | `/schemes/{code}` | Scheme detail + document checklist |

## Matching
| POST | `/match` | Profile in → ranked eligible schemes + reasons out |
| POST | `/match/explain` | Plain-language explanation for one match |
| GET  | `/match/{id}/trace` | Full audit trace of a decision |

## Channel partners
| GET  | `/partners` | Filter by type, state, district, loan_category |
| GET  | `/partners/nearby` | `?lat=&lon=&loan_category=&radius_km=` |
| GET  | `/partners/{id}` | Partner detail, contact, categories handled |

## Applications
| POST | `/applications` | Start an application against a scheme + partner |
| GET  | `/applications/{id}` | Status |
| POST | `/applications/{id}/documents` | Upload document |

## Assistant
| POST | `/assistant/chat` | Conversational Q&A grounded in the scheme corpus |
| POST | `/assistant/voice` | Audio in → transcript + intent |
