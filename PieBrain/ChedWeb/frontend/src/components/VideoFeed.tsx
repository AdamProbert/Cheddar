/**
 * Video display component with Satisfactory-themed industrial design
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
    <Card className="w-full aspect-video bg-black flex items-center justify-center overflow-hidden relative">
      {/* Decorative corner brackets */}
      <div className="absolute top-2 left-2 w-6 h-6 border-t-2 border-l-2 border-satisfactory-orange"></div>
      <div className="absolute top-2 right-2 w-6 h-6 border-t-2 border-r-2 border-satisfactory-orange"></div>
      <div className="absolute bottom-2 left-2 w-6 h-6 border-b-2 border-l-2 border-satisfactory-orange"></div>
      <div className="absolute bottom-2 right-2 w-6 h-6 border-b-2 border-r-2 border-satisfactory-orange"></div>
      
      {videoStream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-contain"
        />
      ) : (
        <div className="text-center text-muted-foreground z-10">
          <div className="text-6xl mb-4 animate-pulse-glow">📹</div>
          <p className="text-lg font-bold uppercase tracking-wider text-satisfactory-orange">No Video Stream</p>
          <p className="text-sm mt-2 text-muted-foreground">[ Connect to initialize feed ]</p>
          <div className="mt-4 flex justify-center gap-2">
            <div className="w-2 h-2 bg-satisfactory-orange rounded-full animate-pulse-glow"></div>
            <div className="w-2 h-2 bg-satisfactory-orange rounded-full animate-pulse-glow" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-satisfactory-orange rounded-full animate-pulse-glow" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      )}
    </Card>
  )
}

