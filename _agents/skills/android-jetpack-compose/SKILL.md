---
name: android-jetpack-compose
description: "Modern Android development with Jetpack Compose. Covers composables, state management, navigation, Material 3 design. Use when: Android app, Compose, modern UI."
source: claude-skills-360
---

# Android Jetpack Compose Guide

**Role**: Android Compose Developer

You build modern, responsive Android apps with Compose's declarative paradigm.
You understand composition and recomposition. You manage state effectively.
You leverage Material 3 for beautiful UIs. You know when Compose excels and
when imperative views are appropriate.

## Capabilities

- Jetpack Compose fundamentals
- Composable functions
- State management with remember and State
- Navigation with Compose
- Material 3 design system
- Theme and styling
- Testing Compose
- Interop with Views

## Patterns

### Hello, Compose

Basic composable

**When to use**: When starting a Compose app

```kotlin
import androidx.compose.foundation.layout.Column
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

@Composable
fun GreetingScreen() {
    Column(modifier = Modifier.fillMaxSize()) {
        Text("Hello, Jetpack Compose!")
        Button(onClick = { }) {
            Text("Click me")
        }
    }
}
```

### State Management

Managing composable state

**When to use**: When handling user interactions

```kotlin
import androidx.compose.material3.OutlinedTextField
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember

@Composable
fun CounterScreen() {
    var count by remember { mutableStateOf(0) }

    Column(modifier = Modifier.padding(16.dp)) {
        Text("Count: $count", style = MaterialTheme.typography.headlineMedium)

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { count-- }) {
                Text("-")
            }
            Button(onClick = { count++ }) {
                Text("+")
            }
        }
    }
}

// With ViewModel
@Composable
fun PostListScreen(viewModel: PostViewModel = viewModel()) {
    val posts by viewModel.posts.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()

    if (isLoading) {
        CircularProgressIndicator()
    } else {
        LazyColumn {
            items(posts) { post ->
                PostCard(post = post)
            }
        }
    }
}
```

### Navigation

Multi-screen apps

**When to use**: When building navigation flow

```kotlin
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController

@Composable
fun MyApp() {
    val navController = rememberNavController()

    NavHost(navController, startDestination = "posts") {
        composable("posts") {
            PostListScreen(
                onPostClick = { postId ->
                    navController.navigate("posts/$postId")
                }
            )
        }

        composable(
            "posts/{postId}",
            arguments = listOf(navArgument("postId") { type = NavType.StringType })
        ) { backStackEntry ->
            val postId = backStackEntry.arguments?.getString("postId")
            PostDetailScreen(
                postId = postId,
                onBack = { navController.popBackStack() }
            )
        }
    }
}
```

### Lists

Efficient list rendering

**When to use**: When displaying lists of items

```kotlin
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items

data class Post(val id: String, val title: String, val content: String)

@Composable
fun PostListScreen(posts: List<Post>) {
    LazyColumn(modifier = Modifier.fillMaxSize()) {
        items(
            items = posts,
            key = { post -> post.id }
        ) { post ->
            PostCard(post = post)
        }
    }
}

@Composable
fun PostCard(post: Post) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(post.title, style = MaterialTheme.typography.headlineSmall)
            Spacer(modifier = Modifier.height(8.dp))
            Text(post.content, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
```

### Material 3 Theme

Styling apps

**When to use**: When applying consistent styling

```kotlin
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.darkColorScheme

private val LightColorScheme = lightColorScheme(
    primary = Color(0xFF6200EE),
    secondary = Color(0xFF03DAC6),
    tertiary = Color(0xFF03DAC6)
)

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFFBB86FC),
    secondary = Color(0xFF03DAC6),
    tertiary = Color(0xFF03DAC6)
)

@Composable
fun MyAppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography(),
        content = content
    )
}

// Usage
@Composable
fun MyApp() {
    MyAppTheme {
        Surface(color = MaterialTheme.colorScheme.background) {
            ContentScreen()
        }
    }
}
```

### Forms and Input

User data entry

**When to use**: When collecting user input

```kotlin
import androidx.compose.material3.OutlinedTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType

@Composable
fun PostFormScreen(onSave: (String, String) -> Unit) {
    var title by remember { mutableStateOf("") }
    var content by remember { mutableStateOf("") }

    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = title,
            onValueChange = { title = it },
            label = { Text("Title") },
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = content,
            onValueChange = { content = it },
            label = { Text("Content") },
            modifier = Modifier
                .fillMaxWidth()
                .height(200.dp),
            maxLines = 5
        )

        Spacer(modifier = Modifier.height(16.dp))

        Button(
            onClick = { onSave(title, content) },
            modifier = Modifier.align(Alignment.End)
        ) {
            Text("Save")
        }
    }
}
```

### Testing

Testing composables

**When to use**: When ensuring correctness

```kotlin
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule

class PostListScreenTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun testPostListDisplaysItems() {
        val posts = listOf(
            Post("1", "First Post", "Content"),
            Post("2", "Second Post", "More content")
        )

        composeTestRule.setContent {
            PostListScreen(posts = posts)
        }

        composeTestRule.onNodeWithText("First Post").assertExists()
        composeTestRule.onNodeWithText("Second Post").assertExists()
    }

    @Test
    fun testButtonClick() {
        var clickCount = 0

        composeTestRule.setContent {
            Button(onClick = { clickCount++ }) {
                Text("Click me")
            }
        }

        composeTestRule.onNodeWithText("Click me").performClick()
        assert(clickCount == 1)
    }
}
```

## Anti-Patterns

### ❌ Recomposing Entire Screen

**Why bad**: Performance degrades.
Expensive calculations run repeatedly.
Janky UI.

**Instead**: Isolate state changes.
Memoize expensive computations.
Use key() for list items.

### ❌ Not Using remember

**Why bad**: State resets on recomposition.
Behavior is unpredictable.
User input is lost.

**Instead**: Always use remember for state.
Understand recomposition boundaries.
Test with preview annotation.

### ❌ Complex Nested Hierarchies

**Why bad**: Hard to maintain.
Difficult to read.
Performance issues.

**Instead**: Extract to separate composables.
Use composition over nesting.
Keep functions small.

## Related Skills

Works well with: `kotlin-fundamentals`, `mobile-app-architecture`, `ui-design`, `testing-strategies`
