import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import api from '@/services/api'

export default function Settings() {
  const { data, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const { data } = await api.get('/settings/')
      return data
    },
  })

  const settings: any[] = data?.items ?? []

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">System configuration</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : (
            <div className="space-y-2">
              {settings.map((s) => (
                <div key={s.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                  <div>
                    <p className="text-sm font-medium">{s.key}</p>
                    <p className="text-xs text-muted-foreground">{s.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{s.category}</Badge>
                    <code className="text-xs bg-background px-2 py-1 rounded">
                      {typeof s.value === 'object' ? JSON.stringify(s.value) : String(s.value)}
                    </code>
                  </div>
                </div>
              ))}
              {settings.length === 0 && (
                <p className="text-center py-8 text-muted-foreground">No settings configured</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
