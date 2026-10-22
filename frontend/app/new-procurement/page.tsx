"use client"

import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Button } from "@/components/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectItem, SelectTrigger, SelectContent, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import DashboardLayout from "@/app/dashboard-layout"
import { api } from "@/lib/api"
import { Plus } from "lucide-react"

const procurementSchema = z.object({
  product_name: z.string().min(2, "Product name is required"),
  category: z.string().min(1, "Category is required"),
  description: z.string().min(10, "Description must be at least 10 characters"),
  quantity: z.coerce.number().min(1, "Quantity must be at least 1"),
  max_budget: z.coerce.number().min(1, "Budget must be greater than 0"),
  currency: z.string().min(3, "Currency is required"),
  required_features: z.string().optional(),
  warranty_months: z.coerce.number().min(1, "Warranty months required"),
  delivery_needed_by: z.string().optional(),
  preferred_vendors: z.string().optional(),
})

type ProcurementFormValues = z.infer<typeof procurementSchema>

const CATEGORIES = [
  "Computers & Laptops",
  "Servers & Infrastructure",
  "Software & Licenses",
  "Office Equipment",
  "Networking",
  "Telecommunications",
  "Furniture",
  "Vehicles",
  "Other",
]

export default function NewProcurementPage() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<ProcurementFormValues>({
    resolver: zodResolver(procurementSchema),
    defaultValues: {
      product_name: "",
      category: "",
      description: "",
      quantity: 1,
      max_budget: 0,
      currency: "USD",
      required_features: "",
      warranty_months: 12,
      delivery_needed_by: "",
      preferred_vendors: "",
    },
  })

  async function onSubmit(values: ProcurementFormValues) {
    setIsSubmitting(true)
    try {
      const payload = {
        product_name: values.product_name,
        category: values.category,
        description: values.description,
        quantity: values.quantity,
        max_budget: values.max_budget,
        currency: values.currency,
        required_features: values.required_features
          ? values.required_features.split(",").map((f) => f.trim()).filter(Boolean)
          : [],
        warranty_months: values.warranty_months,
        delivery_needed_by: values.delivery_needed_by || undefined,
        preferred_vendors: values.preferred_vendors
          ? values.preferred_vendors.split(",").map((v) => v.trim()).filter(Boolean)
          : [],
      }

      const res = await api.post<{ id: string }>("/procurement-requests", payload)

      toast.success("Procurement request created", {
        description: "An Officer can now start the agent pipeline.",
      })
      router.push(`/requests/${res.id}`)
    } catch (err: any) {
      toast.error("Failed to create request", {
        description: err?.message || "Please try again.",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <DashboardLayout title="New Procurement Request" breadcrumbs={["New Procurement"]}>
      <div className="max-w-3xl mx-auto">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-foreground">New Procurement Request</h1>
            <p className="text-muted-foreground">
              Submit your procurement requirements to initiate the eight-agent evaluation and negotiation workflow.
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Procurement Intake Form</CardTitle>
            <CardDescription>
              Provide detailed requirements so our agents can find the best vendor for your needs.
            </CardDescription>
          </CardHeader>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <CardContent>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="product_name">Product or Service Name</Label>
                    <Input
                      id="product_name"
                      {...form.register("product_name")}
                      placeholder="e.g. Enterprise Laptop"
                    />
                    {form.formState.errors.product_name && (
                      <p className="text-sm text-destructive">{form.formState.errors.product_name.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Controller
                      name="category"
                      control={form.control}
                      render={({ field }) => (
                        <Select value={field.value} onValueChange={field.onChange}>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Select a category" />
                          </SelectTrigger>
                          <SelectContent>
                            {CATEGORIES.map((cat) => (
                              <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {form.formState.errors.category && (
                      <p className="text-sm text-destructive">{form.formState.errors.category.message}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Detailed Requirements</Label>
                  <Textarea
                    id="description"
                    {...form.register("description")}
                    rows={4}
                    placeholder="Describe the product/service requirements in detail..."
                  />
                  {form.formState.errors.description && (
                    <p className="text-sm text-destructive">{form.formState.errors.description.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="quantity">Quantity</Label>
                    <Input
                      id="quantity"
                      type="number"
                      {...form.register("quantity")}
                      placeholder="1"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="max_budget">Max Budget</Label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
                      <Input
                        id="max_budget"
                        type="number"
                        {...form.register("max_budget")}
                        placeholder="0.00"
                        className="pl-8"
                      />
                    </div>
                    {form.formState.errors.max_budget && (
                      <p className="text-sm text-destructive">{form.formState.errors.max_budget.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Currency</Label>
                    <Controller
                      name="currency"
                      control={form.control}
                      render={({ field }) => (
                        <Select value={field.value} onValueChange={field.onChange}>
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="USD">USD</SelectItem>
                            <SelectItem value="EUR">EUR</SelectItem>
                            <SelectItem value="GBP">GBP</SelectItem>
                            <SelectItem value="INR">INR</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="delivery_needed_by">Delivery Needed By</Label>
                    <Input
                      id="delivery_needed_by"
                      type="date"
                      {...form.register("delivery_needed_by")}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="warranty_months">Warranty (Months)</Label>
                    <Input
                      id="warranty_months"
                      type="number"
                      {...form.register("warranty_months")}
                      placeholder="12"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="required_features">Required Features</Label>
                    <Input
                      id="required_features"
                      {...form.register("required_features")}
                      placeholder="wifi, bluetooth, warranty, fast-delivery"
                      className="text-sm"
                    />
                    <p className="text-xs text-muted-foreground">
                      Comma-separated list of required product features.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="preferred_vendors">Preferred Vendors</Label>
                    <Input
                      id="preferred_vendors"
                      {...form.register("preferred_vendors")}
                      placeholder="vendor-a, vendor-b"
                      className="text-sm"
                    />
                    <p className="text-xs text-muted-foreground">
                      Comma-separated list of preferred vendor names.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
            <div className="p-6 pt-0">
              <Button type="submit" disabled={isSubmitting} className="w-full">
                {isSubmitting ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                    Creating Request...
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <Plus className="w-4 h-4" />
                    Create Procurement Request
                  </div>
                )}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </DashboardLayout>
  )
}