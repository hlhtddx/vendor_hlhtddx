package hlhtddx

import (
	"android/soong/android"
	"github.com/google/blueprint"
	"android/soong/cc"
	"fmt"
	"strings"
)

// This singleton generates CMakeLists.txt files. It does so for each blueprint Android.bp resulting in a cc.Module
// when either make, mm, mma, mmm or mmma is called. CMakeLists.txt files are generated in a separate folder
// structure (see variable CLionOutputProjectsDirectory for root).

func init() {
	android.RegisterSingletonType("cdt_project", cDTProjectGeneratorSingleton)
}

func cDTProjectGeneratorSingleton() blueprint.Singleton {
	return &cdtProjectsGeneratorSingleton{}
}

type cdtProjectsGeneratorSingleton struct{}

func (c *cdtProjectsGeneratorSingleton) GenerateBuildActions(ctx blueprint.SingletonContext) {
	ctx.VisitAllModules(func(module blueprint.Module) {
		if ccModule, ok := module.(*cc.Module); ok {
			if ccModule.DeviceSupported() && ccModule.Enabled() && ccModule.TargetPrimary() {
				if strings.Contains(ctx.ModuleType(module), "test") {
					return
				}
				fmt.Printf("Module: Name=%s, Type=%s\n", ccModule.Name(), ctx.ModuleType(module))
				fmt.Printf("\tPath=%s SubDir=%s\n", ctx.ModuleDir(module), ctx.ModuleSubDir(module))
				fmt.Printf("\tBpFile=%s\n", ctx.BlueprintFile(module))
			}
		}
		if srcProducer, ok := module.(android.SourceFileProducer); ok {
			fmt.Println("Src = ", srcProducer.Srcs())
		}
	})
	return
}
