import { SavedState } from './models';
import data from '../../shared/demo-state.json';
export const initialState = (): SavedState => structuredClone(data) as SavedState;
