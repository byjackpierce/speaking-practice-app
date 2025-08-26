# Translation Feature Implementation Plan

## 🎯 Goal
Add translation functionality to Portuguese Gap-Capture app with interactive highlights and flashcards.

## 📋 Two Main Features

### 1. Interactive Transcript with Hover Translations
- **Input:** Grammar-corrected transcript with mixed languages
- **Output:** HTML with English sections highlighted
- **Interaction:** Hover over English → Portuguese translation popup
- **Example:** "Vamos fazer uma prova **to see if it works** Vamos lá"
- **Hover:** "to see if it works" → "para ver se funciona"

### 2. Complete Sentence Flashcards
- **Input:** Original transcript + English segments
- **Output:** Two versions of each sentence
- **Format:** 
  - **Original:** "Vamos fazer uma prova **to see if it works** Vamos lá"
  - **Translated:** "Vamos fazer uma prova **para ver se funciona** Vamos lá"

## 🔧 Implementation Steps

### Phase 1: Backend Translation
1. Extract English segments from transcription results
2. Translate English segments to Portuguese
3. Add translations to API response

### Phase 2: Frontend Display
1. Highlight English sections in transcript
2. Add hover functionality for translations
3. Create flashcard display below transcript

### Phase 3: Polish & Testing
1. Style highlights and popups
2. Test with various sentence structures
3. Optimize performance

## 🎯 Next Step
Start with Phase 1: Backend translation functions
