const ytpl = require('ytpl');
const ytdl = require('ytdl-core');

async function getVideoUrls(playlistOrVideoUrl) {
    try {
        if (ytpl.validateID(playlistOrVideoUrl)) {
            const playlistInfo = await ytpl(playlistOrVideoUrl);
            const videos = playlistInfo.items.map(item => ({ url: item.shortUrl, name: item.title }));
            console.log(JSON.stringify(videos));
        } else if (ytdl.validateURL(playlistOrVideoUrl)) {
            const videoInfo = await ytdl.getInfo(playlistOrVideoUrl);
            const video = { url: videoInfo.videoDetails.video_url, name: videoInfo.videoDetails.title };
            console.log(JSON.stringify([video]));
        } else {
            console.error('Invalid URL:', playlistOrVideoUrl);
        }
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Example usage:
//    const playlistOrVideoUrl = process.argv[2];
//    getVideoUrls(playlistOrVideoUrl);
