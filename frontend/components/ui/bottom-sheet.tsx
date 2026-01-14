"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { motion, AnimatePresence, useDragControls, PanInfo } from "framer-motion";
import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks/use-mobile";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./dialog";

interface BottomSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  title?: string;
  description?: string;
  /** Whether to show the drag handle indicator */
  showHandle?: boolean;
  /** Custom className for the content */
  className?: string;
}

/**
 * BottomSheet component that renders as a bottom sheet on mobile
 * and as a standard dialog on desktop.
 */
export function BottomSheet({
  open,
  onOpenChange,
  children,
  title,
  description,
  showHandle = true,
  className,
}: BottomSheetProps) {
  const isMobile = useIsMobile();
  const dragControls = useDragControls();

  // Use standard dialog on desktop
  if (!isMobile) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className={className}>
          {title && (
            <DialogHeader>
              <DialogTitle>{title}</DialogTitle>
              {description && <DialogDescription>{description}</DialogDescription>}
            </DialogHeader>
          )}
          {children}
        </DialogContent>
      </Dialog>
    );
  }

  const handleDragEnd = (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    // Close if dragged down fast enough or far enough
    if (info.velocity.y > 500 || info.offset.y > 150) {
      onOpenChange(false);
    }
  };

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <AnimatePresence>
        {open && (
          <DialogPrimitive.Portal forceMount>
            {/* Overlay */}
            <DialogPrimitive.Overlay asChild>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="fixed inset-0 z-50 bg-black/50"
                onClick={() => onOpenChange(false)}
              />
            </DialogPrimitive.Overlay>

            {/* Content */}
            <DialogPrimitive.Content asChild>
              <motion.div
                initial={{ y: "100%" }}
                animate={{ y: 0 }}
                exit={{ y: "100%" }}
                transition={{ type: "spring", damping: 30, stiffness: 300 }}
                drag="y"
                dragControls={dragControls}
                dragConstraints={{ top: 0 }}
                dragElastic={0.2}
                onDragEnd={handleDragEnd}
                className={cn(
                  "fixed bottom-0 left-0 right-0 z-50",
                  "bg-background rounded-t-2xl shadow-xl",
                  "max-h-[90vh] overflow-hidden",
                  "safe-area-bottom",
                  className
                )}
              >
                {/* Drag handle */}
                {showHandle && (
                  <div
                    className="flex justify-center py-3 cursor-grab active:cursor-grabbing"
                    onPointerDown={(e) => dragControls.start(e)}
                  >
                    <div className="w-10 h-1 rounded-full bg-muted-foreground/30" />
                  </div>
                )}

                {/* Header */}
                {title && (
                  <div className="px-6 pb-4 border-b">
                    <DialogPrimitive.Title className="text-lg font-semibold">
                      {title}
                    </DialogPrimitive.Title>
                    {description && (
                      <DialogPrimitive.Description className="text-sm text-muted-foreground mt-1">
                        {description}
                      </DialogPrimitive.Description>
                    )}
                  </div>
                )}

                {/* Content */}
                <div className="overflow-y-auto max-h-[calc(90vh-100px)] p-6">
                  {children}
                </div>
              </motion.div>
            </DialogPrimitive.Content>
          </DialogPrimitive.Portal>
        )}
      </AnimatePresence>
    </DialogPrimitive.Root>
  );
}

/**
 * BottomSheetTrigger - wraps DialogPrimitive.Trigger
 */
export const BottomSheetTrigger = DialogPrimitive.Trigger;

/**
 * BottomSheetClose - wraps DialogPrimitive.Close
 */
export const BottomSheetClose = DialogPrimitive.Close;
