
async function poll() {
  const res  = await fetch('/now-playing')
  const data = await res.json()
  console.log(data)  
}

poll()
setInterval(poll, 3000)

document.getElementById('title').textContent = data.title
document.getElementById('artist').textContent = data.artist
document.getElementById('art').src = data.album_art