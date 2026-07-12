def _keep_last_repeated_block(text: str, min_block_chars: int = 20) -> str:
    """
    Repair text mangled by a streaming bug that re-sends the message
    from the beginning one or more times, where the final, complete
    version of the message ends up appearing twice in a row.

    Observed shape (this is what the bug produces):

        "<partial><longer partial>...<complete><complete>"

    i.e. a series of ever-growing prefixes of the real answer,
    directly concatenated with no separator, ending with the
    complete answer duplicated back-to-back.

    Approach
    --------
    Scan for the LARGEST block length L such that the last L
    characters of `text` are an exact, immediate repeat of the L
    characters right before them::

        text[-2L : -L] == text[-L:]

    That trailing duplicated block is the complete, correct message.
    Returning just one copy of it automatically discards every
    earlier, truncated restart too -- there's no need to separately
    detect or account for each partial chunk that came before it.

    We search from the largest possible L down to `min_block_chars`
    and stop at the first (i.e. largest) match, so a big genuine
    duplicated answer is always found before any small, incidental
    repeat (e.g. a repeated word) could be mistaken for it.

    Safety
    ------
    If no repeated block of at least `min_block_chars` characters is
    found, `text` is returned completely unchanged. This is
    deliberately conservative: it's far safer to leave a rare,
    undetected duplication in place than to risk cutting real content
    out of a message that was never affected by this bug.

    Parameters
    ----------
    text : str
        The possibly-duplicated text to repair.
    min_block_chars : int, optional
        Minimum length (in characters) a trailing duplicated block
        must have before it's treated as a genuine repeat rather than
        coincidental short repetition (e.g. "the the"). Defaults to 20.

    Returns
    -------
    str
        The repaired text (a single clean copy of the final block),
        or the original text if no qualifying duplication is found.
    """
    n = len(text)
    if n < min_block_chars * 2:
        return text

    # Try the largest possible block first; the first match we find
    # (scanning from big L to small L) is the correct, complete one.
    for block_len in range(n // 2, min_block_chars - 1, -1):
        split = n - block_len
        if text[split - block_len:split] == text[split:]:
            return text[split:]

    return text

sample_1 = "Hey thereHey there! How's it going? What's on your mind today?Hey there! How's it going? What's on your mind today?"

sample_2 = """To addTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) projectTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.ktsTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

###To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.ktsTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependenciesTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implementTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project withTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project with Gradle files, and you're ready to run it on Android, iOS, or any other supported KMP targets.To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project with Gradle files, and you're ready to run it on Android, iOS, or any other supported KMP targets."""

sample_3 = """The capitalThe capital of France is **Paris**. 

It is located in the north-central part of the countryThe capital of France is **Paris**. 

It is located in the north-central part of the country, along the Seine River.The capital of France is **Paris**. 

It is located in the north-central part of the country, along the Seine River."""

sample_4 = """Here isHere is the quickest way to create and run a "Hello, World!" application in .NET usingHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new consoleHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
NavigateHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.csHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the applicationHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
```text
Hello, World!
```Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
```text
Hello, World!
```"""

sample_5 = """Right?Right? I like to think so. 

What's on your mind? How can I help you outRight? I like to think so. 

What's on your mind? How can I help you out today?Right? I like to think so. 

What's on your mind? How can I help you out today?"""

print("sample 1: \n")
print(_keep_last_repeated_block(sample_1))

print("\n \n")
print("sample 2: \n")
print(_keep_last_repeated_block(sample_2))

print("\n \n")
print("sample 3: \n")
print(_keep_last_repeated_block(sample_3))

print("\n \n")
print("sample 4: \n")
print(_keep_last_repeated_block(sample_4))

print("\n \n")
print("sample 5: \n")
print(_keep_last_repeated_block(sample_5))