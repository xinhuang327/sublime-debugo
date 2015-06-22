import sublime, sublime_plugin
import string
import os

breakpointText = '_ = "breakpoint"'
instrumentPkgsToken = "{{InstrumentPkgs}}"

class AddGoBreakpointCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		# Walk through each region in the selection
		for region in view.sel():
			# Only interested in empty regions, otherwise they may span multiple
			# lines, which doesn't make sense for this command.
			if region.empty():
				# Expand the region to the full line it resides on, excluding the newline
				line = view.line(region)
				prevLine = view.line(line.begin()-1)
				prevLineContents = view.substr(prevLine)
				prevLinetextContent = prevLineContents.lstrip(string.whitespace)
				lineContents = view.substr(line)
				textContent = lineContents.lstrip(string.whitespace)
				if prevLinetextContent == breakpointText:
					# remove previous breakpoint
					prevLine.b = prevLine.b+1
					view.erase(edit, prevLine)
				elif textContent == breakpointText:
					line.b = line.b+1
					view.erase(edit, line)
				else:
					# add breakpoint line before current line
					newLineContent = lineContents.replace(textContent, breakpointText+"\n")
					# Add the text at the beginning of the line
					view.insert(edit, line.begin(), newLineContent)

pkgsSet = set()
filesSet = set()

def updateBreakpointInfo(view):
	filePath = view.file_name()
	if not filePath.endswith(".go"):
		return
	bpRegion = view.find(breakpointText, 0)
	print(bpRegion)
	pkgPath = getPkgPathForFile(filePath)
	if bpRegion.empty():
		# remove from breakpoint file list
		print(filePath, "no breakpoint found")
		if pkgPath in pkgsSet:
			pkgsSet.remove(pkgPath)
		if filePath in filesSet:
			filesSet.remove(filePath)
	else:
		# add to breakpoint file list
		print(filePath, "has breakpoint")
		pkgsSet.add(pkgPath)
		filesSet.add(filePath)
	print("pkgsSet", pkgsSet)
	print("filesSet", filesSet)

def getPkgPathForFile(filePath):
	prefix = "github.com"
	idx = filePath.index(prefix)
	subPath = filePath[idx:]
	ridx = subPath.rindex("\\")
	pkgPath = subPath[:ridx]
	return pkgPath.replace("\\","/") #returns github.com/.../pkgname

buildFileName = "xinhuang327_web_musictree_web.sublime-build"

class EventDump(sublime_plugin.EventListener):
	def on_load(self, view):
		updateBreakpointInfo(view)

	def on_pre_save(self, view):
		updateBreakpointInfo(view)

	def on_post_save(self, view):
		buildFilePath = os.path.join(sublime.packages_path(), "User\\"+buildFileName)
		f = open(buildFilePath, 'w')
		f.write(buildFileTemplate)
		f.close()
 
buildFileTemplate = """{
	"shell_cmd": "echo Kill running process... &taskkill /F /FI \\\"WindowTitle eq Run Release\\\" /T & echo BUILDING Release... & go build & echo DONE & start \\\"Run Release\\\" cmd /c \\\"web.exe & pause\\\"",
	"working_dir": "${project_path:${folder}}\\\\..\\\\music_tree\\\\web",

	"variants": [
		{   
			"shell_cmd": "echo Kill running process... &taskkill /F /FI \\\"WindowTitle eq Run Debug\\\" /T & echo BUILDING Debug... & godebug build {{InstrumentPkgs}} main.go & echo DONE & start \\\"Run Debug\\\" cmd /c \\\"main.debug & pause\\\"",
			"shell": true,
			"name": "Build And Run Debug"
		},
		{   
			"shell_cmd": "echo BUILDING Release... & go build & echo DONE",
			"shell": true,
			"name": "Build Release"
		},
		{   
			"name": "- - - - - - - - -"
		},
		{   
			"shell_cmd": "echo Kill running process... &taskkill /F /FI \\\"WindowTitle eq Run Debug\\\" /T & start \\\"Run Debug\\\" cmd /c \\\"main.debug & pause\\\"",
			"shell": true,
			"name": "Run Debug"
		},
		{   
			"shell_cmd": "start \\\"Run Release\\\" cmd /c \\\"web.exe & pause\\\"",
			"shell": true,
			"name": "Run Release"
		}
	]
}"""