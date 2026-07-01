import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Brain, Play, Activity } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { mlApi } from '@/services/api'
import toast from 'react-hot-toast'
import { useState } from 'react'
import type { MLModel } from '@/types'

export default function ML() {
  const queryClient = useQueryClient()
  const [datasetPath, setDatasetPath] = useState('')

  const { data: models = [], isLoading } = useQuery<MLModel[]>({
    queryKey: ['ml-models'],
    queryFn: async () => {
      const { data } = await mlApi.models()
      return data
    },
  })

  const trainMutation = useMutation({
    mutationFn: (path: string) => mlApi.train(path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ml-models'] })
      toast.success('Model training started')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message || 'Training failed')
    },
  })

  const activateMutation = useMutation({
    mutationFn: (id: string) => mlApi.activateModel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ml-models'] })
      toast.success('Model activated')
    },
  })

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Machine Learning</h1>
        <p className="text-sm text-muted-foreground">ML model management and training</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Train New Model</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <input
              type="text"
              value={datasetPath}
              onChange={(e) => setDatasetPath(e.target.value)}
              placeholder="Path to dataset (e.g., datasets/cicids2017.csv)"
              className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm"
            />
            <Button onClick={() => trainMutation.mutate(datasetPath)} disabled={!datasetPath || trainMutation.isPending}>
              <Play className="h-4 w-4 mr-2" />
              {trainMutation.isPending ? 'Training...' : 'Start Training'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Trained Models ({models.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : (
            <div className="space-y-3">
              {models.map((model) => (
                <div key={model.id} className="p-4 rounded-lg border border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Brain className="h-5 w-5 text-primary" />
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{model.name}</h3>
                          {model.is_active && <Badge variant="success">Active</Badge>}
                          {model.is_trained ? <Badge variant="info">Trained</Badge> : <Badge variant="warning">Untrained</Badge>}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {model.model_type} | v{model.version} | Acc: {model.accuracy ? (model.accuracy * 100).toFixed(1) : 'N/A'}%
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {model.is_trained && !model.is_active && (
                        <Button variant="outline" size="sm" onClick={() => activateMutation.mutate(model.id)}>
                          <Activity className="h-4 w-4 mr-1" /> Activate
                        </Button>
                      )}
                    </div>
                  </div>
                  {model.f1_macro && (
                    <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
                      <span>F1: {(model.f1_macro * 100).toFixed(1)}%</span>
                      {model.training_samples && <span>Samples: {model.training_samples.toLocaleString()}</span>}
                      {model.training_dataset && <span>Dataset: {model.training_dataset}</span>}
                    </div>
                  )}
                </div>
              ))}
              {models.length === 0 && (
                <p className="text-center py-8 text-muted-foreground">No models trained yet</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
