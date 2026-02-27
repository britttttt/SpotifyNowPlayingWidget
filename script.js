let lastTitle = ''

async function poll() {
  const res  = await fetch('/now-playing')
  const data = await res.json()

  if (data && data.title) {
    const isPlaying = data.is_playing
    console.log('is_playing:', isPlaying)
    
    if (isPlaying) {
      document.getElementById('card').classList.remove('hidden')
    } else {
      document.getElementById('card').classList.add('hidden')
    }

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