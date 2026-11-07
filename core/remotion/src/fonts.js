import {continueRender, delayRender} from 'remotion';

// Chờ font tải xong để khung đầu không bị nhảy chữ.
const handle = typeof document !== 'undefined' ? delayRender('fonts') : null;
if (handle !== null) {
  document.fonts.ready.then(() => continueRender(handle));
}
export const FONT = '"Be Vietnam Pro", sans-serif';
