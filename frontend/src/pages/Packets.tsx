import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { packetsApi } from '@/services/api'
import type { Packet } from '@/types'

export default function Packets() {
  const { data, isLoading } = useQuery({
    queryKey: ['packets'],
    queryFn: async () => {
      const { data } = await packetsApi.list({ page: 1, page_size: 50 })
      return data
    },
    refetchInterval: 5000,
  })

  const packets: Packet[] = data?.items ?? []

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Live Packets</h1>
        <p className="text-sm text-muted-foreground">Real-time packet capture data</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Captured Packets ({data?.total ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 font-medium">Time</th>
                    <th className="text-left py-3 font-medium">Protocol</th>
                    <th className="text-left py-3 font-medium">Source</th>
                    <th className="text-left py-3 font-medium">Destination</th>
                    <th className="text-right py-3 font-medium">Size</th>
                    <th className="text-left py-3 font-medium">Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {packets.map((p) => (
                    <tr key={p.id} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                      <td className="py-2 text-muted-foreground">
                        {new Date(p.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-2">
                        <Badge variant="outline" className="text-xs">{p.protocol}</Badge>
                      </td>
                      <td className="py-2 font-mono text-xs">{p.src_ip}:{p.src_port ?? '-'}</td>
                      <td className="py-2 font-mono text-xs">{p.dst_ip}:{p.dst_port ?? '-'}</td>
                      <td className="py-2 text-right">{p.packet_size} B</td>
                      <td className="py-2 text-xs font-mono">{p.tcp_flags || '-'}</td>
                    </tr>
                  ))}
                  {packets.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-muted-foreground">
                        No packets captured yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
