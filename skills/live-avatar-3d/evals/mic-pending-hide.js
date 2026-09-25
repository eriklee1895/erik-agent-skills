// Run in a browser tab after opening avatar-template.html via:
// agent-browser --session <name> eval --stdin < skills/live-avatar-3d/evals/mic-pending-hide.js
// This stubs getUserMedia; it never requests a real microphone permission.
(async () => {
  const mediaDevices = navigator.mediaDevices;
  if (!mediaDevices?.getUserMedia) throw new Error('getUserMedia is unavailable in this browser');

  const originalGetUserMedia = Object.getOwnPropertyDescriptor(mediaDevices, 'getUserMedia');
  const originalHidden = Object.getOwnPropertyDescriptor(document, 'hidden');
  const originalAudioContext = Object.getOwnPropertyDescriptor(window, 'AudioContext');
  const originalWebkitAudioContext = Object.getOwnPropertyDescriptor(window, 'webkitAudioContext');
  let resolveRequest;
  let stoppedTracks = 0;
  let audioContextsCreated = 0;
  const fakeTrack = { stop() { stoppedTracks += 1; }, addEventListener() {} };
  const fakeStream = { getTracks: () => [fakeTrack], getAudioTracks: () => [fakeTrack] };

  try {
    Object.defineProperty(mediaDevices, 'getUserMedia', {
      configurable: true,
      value: () => new Promise(resolve => { resolveRequest = resolve; })
    });
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
    Object.defineProperty(window, 'AudioContext', {
      configurable: true,
      value: class {
        constructor() { audioContextsCreated += 1; this.state = 'running'; }
        createAnalyser() {
          return { fftSize: 512, getByteTimeDomainData(buffer) { buffer.fill(128); } };
        }
        createMediaStreamSource() { return { connect() {} }; }
        close() { this.state = 'closed'; return Promise.resolve(); }
      }
    });

    const button = document.querySelector('#mic-button');
    button.click();
    await new Promise(resolve => setTimeout(resolve, 0));
    if (!resolveRequest) throw new Error('microphone request did not start');

    Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
    document.dispatchEvent(new Event('visibilitychange'));
    resolveRequest(fakeStream);
    await new Promise(resolve => setTimeout(resolve, 30));

    const result = {
      stoppedTracks,
      audioContextsCreated,
      pressed: button.getAttribute('aria-pressed'),
      disabled: button.disabled,
      micStatus: document.querySelector('#mic-status').textContent.trim()
    };
    if (result.stoppedTracks !== 1) throw new Error(`expected late stream to stop once; got ${result.stoppedTracks}`);
    if (result.audioContextsCreated !== 0) throw new Error(`audio context started after cancellation: ${result.audioContextsCreated}`);
    if (result.pressed !== 'false' || result.disabled) throw new Error('microphone button did not return to its off state');
    if (result.micStatus !== 'Microphone is off.') throw new Error(`unexpected status: ${result.micStatus}`);
    return JSON.stringify(result);
  } finally {
    if (stoppedTracks === 0) fakeTrack.stop();
    if (originalGetUserMedia) Object.defineProperty(mediaDevices, 'getUserMedia', originalGetUserMedia);
    else delete mediaDevices.getUserMedia;
    if (originalHidden) Object.defineProperty(document, 'hidden', originalHidden);
    else delete document.hidden;
    if (originalAudioContext) Object.defineProperty(window, 'AudioContext', originalAudioContext);
    else delete window.AudioContext;
    if (originalWebkitAudioContext) Object.defineProperty(window, 'webkitAudioContext', originalWebkitAudioContext);
    else delete window.webkitAudioContext;
  }
})()
