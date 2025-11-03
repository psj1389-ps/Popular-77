import { createContext, useContext } from 'react';
import RootStore from './RootStore';

const StoreContext = createContext();

export const StoreProvider = ({ children }) => {
  const store = RootStore.create({});
  
  return (
    <StoreContext.Provider value={store}>
      {children}
    </StoreContext.Provider>
  );
};

export const useStore = () => {
  const store = useContext(StoreContext);
  if (!store) {
    throw new Error('useStore must be used within a StoreProvider');
  }
  return store;
};

export default StoreContext;