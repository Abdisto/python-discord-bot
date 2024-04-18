const axios = require('axios');

async function getVideoUrls(playlistOrVideoUrl, apikey) {
    try {
        const videoRegex = /(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})/;
        const playlistRegex = /(?:https?:\/\/)?(?:www\.)?youtube\.com\/playlist\?list=([a-zA-Z0-9_-]+)/;
        const videoMatch = playlistOrVideoUrl.match(videoRegex);
        const playlistMatch = playlistOrVideoUrl.match(playlistRegex);
        const apiKey = apikey;

        if (playlistMatch) {
            const playlistId = playlistMatch[1];
            const response = await axios.get(`https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=${playlistId}&key=${apiKey}`);
            const videos = response.data.items.map(item => ({ url: `https://www.youtube.com/watch?v=${item.snippet.resourceId.videoId}`, name: item.snippet.title }));
            console.log(JSON.stringify(videos));
        } else if (videoMatch) {
            const videoId = videoMatch[1];
            const response = await axios.get(`https://www.googleapis.com/youtube/v3/videos?part=snippet&id=${videoId}&key=${apiKey}`);
            const video = { url: `https://www.youtube.com/watch?v=${response.data.items[0].id}`, name: response.data.items[0].snippet.title };
            console.log(JSON.stringify([video]));
        } else {
            const videoId = playlistOrVideoUrl.split('v=')[1];
            const response = await axios.get(`https://www.googleapis.com/youtube/v3/videos?part=snippet&id=${videoId}&key=${apiKey}`);
            const video = { url: playlistOrVideoUrl, name: response.data.items[0].snippet.title };
            console.log(JSON.stringify([video]));
        }
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Example usage:
const playlistOrVideoUrl = process.argv[2];
const apikey = process.argv[3];
getVideoUrls(playlistOrVideoUrl, apikey);