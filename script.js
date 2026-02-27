let lastTitle = ''

async function poll() {
  const res  = await fetch('/now-playing')
  const data = await res.json()

  if (data && data.title) {
    if (data.title !== lastTitle){
      animateTrackChange()
      lastTitle = data.title
    }
    document.getElementById('title').textContent  = data.title
    document.getElementById('artist').textContent = data.artist
    document.getElementById('art').src = data.album_art
  }
}

function animateTrackChange() {
  const card = document.getElementById('card')
  card.classList.remove('track-change')
  void card.offsetWidth
  card.classList.add('track-change')
}

poll()
setInterval(poll, 3000)