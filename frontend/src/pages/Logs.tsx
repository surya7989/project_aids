import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import api from '@/services/api'

export default function Logs() {
  const { data, isLoading } = useQuery({
    queryKey: ['logs'],
    queryFn: async () => {
      const { data } = await api.get('/logs/', { params: { page: 1, page_size: 100 } })
      return data
    },
    refetchInterval: 10000,
  })

  const logs: any[] = data?.items ?? []

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Audit Logs</h1>
        <p className="text-sm text-muted-foreground">System audit trail</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Activity Log ({data?.total ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : (
            <div className="space-y-2">
              {logs.map((log: any) => (
                <div key={log.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-secondary/30 text-sm gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={log.status === 'success' ? 'success' : 'danger'} className="text-[10px]">
                      {log.status}
                    </Badge>
                    <span className="font-medium">{log.action}</span>
                    <span className="text-muted-foreground">{log.resource}</span>
                    {log.ip_address && (
                      <span className="text-muted-foreground text-xs font-mono">({log.ip_address})</span>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground self-start sm:self-auto pl-1 sm:pl-0">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
              {logs.length === 0 && (
                <p className="text-center py-8 text-muted-foreground">No logs available</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
