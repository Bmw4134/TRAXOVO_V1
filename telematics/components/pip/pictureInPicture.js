// PiP support
function enablePiP(videoEl) {
  if (!document.pictureInPictureElement) {
    videoEl.requestPictureInPicture().catch(err => console.error('PiP error:', err));
  }
}
