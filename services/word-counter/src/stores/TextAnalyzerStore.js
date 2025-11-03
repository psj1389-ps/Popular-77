import { types } from 'mobx-state-tree';

const TextAnalyzerStore = types
  .model('TextAnalyzerStore', {
    text: types.optional(types.string, ''),
    characterLimit: types.optional(types.number, 5000),
    showCharacterCount: types.optional(types.boolean, true),
    showWordCount: types.optional(types.boolean, true),
    showParagraphCount: types.optional(types.boolean, true),
    showSentenceCount: types.optional(types.boolean, true),
    showReadingTime: types.optional(types.boolean, true),
  })
  .views((self) => ({
    get characterCount() {
      return self.text.length;
    },
    get characterCountNoSpaces() {
      return self.text.replace(/\s/g, '').length;
    },
    get wordCount() {
      if (!self.text.trim()) return 0;
      return self.text.trim().split(/\s+/).length;
    },
    get paragraphCount() {
      if (!self.text.trim()) return 0;
      return self.text.split(/\n\s*\n/).filter(p => p.trim().length > 0).length;
    },
    get sentenceCount() {
      if (!self.text.trim()) return 0;
      return self.text.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
    },
    get readingTime() {
      const wordsPerMinute = 200;
      const minutes = Math.ceil(self.wordCount / wordsPerMinute);
      return minutes;
    },
    get averageWordsPerSentence() {
      if (self.sentenceCount === 0) return 0;
      return Math.round(self.wordCount / self.sentenceCount * 10) / 10;
    },
  }))
  .actions((self) => ({
    setText(newText) {
      if (newText.length <= self.characterLimit) {
        self.text = newText;
      }
    },
    clearText() {
      self.text = '';
    },
    setCharacterLimit(limit) {
      self.characterLimit = limit;
      if (self.text.length > limit) {
        self.text = self.text.substring(0, limit);
      }
    },
    toggleCharacterCount() {
      self.showCharacterCount = !self.showCharacterCount;
    },
    toggleWordCount() {
      self.showWordCount = !self.showWordCount;
    },
    toggleParagraphCount() {
      self.showParagraphCount = !self.showParagraphCount;
    },
    toggleSentenceCount() {
      self.showSentenceCount = !self.showSentenceCount;
    },
    toggleReadingTime() {
      self.showReadingTime = !self.showReadingTime;
    },
  }));

export default TextAnalyzerStore;