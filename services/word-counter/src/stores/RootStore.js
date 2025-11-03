import { types } from 'mobx-state-tree';
import TextAnalyzerStore from './TextAnalyzerStore';

const RootStore = types
  .model('RootStore', {
    textAnalyzer: types.optional(TextAnalyzerStore, {}),
  });

export default RootStore;