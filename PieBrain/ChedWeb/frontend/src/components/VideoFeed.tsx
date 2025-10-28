/**
 * Video display component with connection controls
 */
import { useRef, useEffect } from 'react'
import { useAppStore } from '@/store'
import { Card } from './ui/Card'

export function VideoFeed() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const videoStream = useAppStore(state => state.videoStream)

  useEffect(() => {
    if (videoRef.current && videoStream) {
      videoRef.current.srcObject = videoStream
    }
  }, [videoStream])

  return (
    <Card className="w-full aspect-video bg-black flex items-center justify-center overflow-hidden">
      {videoStream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-contain"
        />
      ) : (
        <div className="text-center text-muted-foreground">
          <div className="text-6xl mb-4">📹</div>
          <p className="text-lg">No video stream</p>
          <p className="text-sm mt-2">Connect to start video feed</p>
          {/* TODO: Video track will be added once camera capture is implemented on backend */}
        </div>
      )}
    </Card>
  )
}
