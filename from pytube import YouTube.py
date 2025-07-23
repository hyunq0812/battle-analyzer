# filename: youtube_video_downloader_video_only.py

import yt_dlp

def download_youtube_video():
    url = input("🔗 유튜브 영상 링크를 입력하세요: ").strip()

    if not url:
        print("❌ 링크를 입력하지 않았습니다.")
        return

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]',            # mp4 영상만 다운로드 (오디오 제외)
        'outtmpl': 'downloaded/%(title)s.%(ext)s', # 저장 경로
        'quiet': False,
        'noplaylist': True
    }

    print("📥 영상 다운로드를 시작합니다 (오디오 없음)...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ 영상 다운로드 완료!")
    except Exception as e:
        print(f"🚨 오류 발생: {e}")

if __name__ == "__main__":
    download_youtube_video()
