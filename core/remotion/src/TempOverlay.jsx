import {AbsoluteFill} from 'remotion';
import {FONT} from './fonts';

// Overlay TẠM cho tới khi chủ kênh đưa overlay.png thật. Overlay nằm trên cùng nên các vùng
// headline/media/emphasis/subtitle trong layout phải trong suốt; chỉ vẽ dải trên và dải dưới safe_bottom.
export const TempOverlay = ({layout, title}) => (
  <AbsoluteFill style={{fontFamily: FONT}}>
    <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 80, background: '#0b1f3a',
      borderBottom: '6px solid #FFD400', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 50px'}}>
      <span style={{color: '#FFD400', fontWeight: 800, fontSize: 32, letterSpacing: 3}}>{title}</span>
      <span style={{color: '#0b1f3a', background: '#FFD400', fontWeight: 800, fontSize: 22, padding: '4px 12px', borderRadius: 6}}>TEMPLATE TẠM</span>
    </div>
    <div style={{position: 'absolute', left: 0, top: layout.media.y - 6, width: 1080, height: 6, background: '#FFD400'}} />
    <div style={{position: 'absolute', left: 0, top: layout.safe_bottom, width: 1080, height: 1920 - layout.safe_bottom,
      background: 'linear-gradient(180deg, rgba(11,31,58,0) 0%, rgba(11,31,58,0.85) 40%)'}} />
  </AbsoluteFill>
);
